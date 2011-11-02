""" Expert prior models"""

import pylab as pl
import pymc as mc

import similarity_prior_model

def level_constraints(name, parameters, unconstrained_mu_age, ages):
    """ Generate PyMC objects implementing priors on the value of the rate function

    Parameters
    ----------
    name : str
    parameters : dict
    unconstrained_mu_age : pymc.Node with values of PCGP

    Results
    -------
    Returns dict of PyMC objects, including 'unconstrained_mu_age' and 'mu_age'
    """
    if 'level_value' not in parameters or 'level_bounds' not in parameters:
        return {}

    @mc.deterministic(name='value_constrained_mu_age_%s'%name)
    def mu_age(unconstrained_mu_age=unconstrained_mu_age,
               value=parameters['level_value']['value'],
               age_before=pl.clip(parameters['level_value']['age_before']-ages[0], 0, len(ages)),
               age_after=pl.clip(parameters['level_value']['age_after']-ages[0], 0, len(ages)),
               lower=parameters['level_bounds']['lower'],
               upper=parameters['level_bounds']['upper']):
        mu_age = unconstrained_mu_age.copy()
        mu_age[:age_before] = value
        if age_after < len(mu_age)-1:
            mu_age[(age_after+1):] = value
        return mu_age.clip(lower, upper)

    mu_sim = similarity_prior_model.similar('value_constrained_mu_age_%s'%name, mu_age, unconstrained_mu_age, 0., .01, 1.e-6)

    return dict(mu_age=mu_age, unconstrained_mu_age=unconstrained_mu_age, mu_sim=mu_sim)


def covariate_level_constraints(name, model, vars, ages):
    """ Generate PyMC objects implementing priors on the value of the covariate adjusted rate function

    Parameters
    ----------
    name : str
    parameters : dict
    unconstrained_mu_age : pymc.Node with values of PCGP

    Results
    -------
    Returns dict of PyMC objects, including 'unconstrained_mu_age' and 'mu_age'
    """
    if name not in model.parameters or 'level_value' not in model.parameters[name] or 'level_bounds' not in model.parameters[name]:
        return {}

    X_out = model.output_template
    X_out['x_sex'] = .5
    for x_i in vars['X_shift'].index:
        X_out[x_i] = pl.array(X_out[x_i], dtype=float) - vars['X_shift'][x_i] # shift covariates so that the root node has X_ar,sr,yr == 0

    X_all = vars['X'].append(X_out.select(lambda c: c in vars['X'].columns, 1), ignore_index=True)
    X_all['x_sex'] = .5 - vars['X_shift']['x_sex']

    X_max = X_all.max()
    X_min = X_all.min()
    X_min['x_sex'] = -.5 - vars['X_shift']['x_sex']  # make sure that the range of sex covariates is included
    
    U_all = [[False for col in vars['U'].columns]]
    nodes = ['all']
    for l in range(1,4):
        nodes = pl.flatten([model.hierarchy.successors(n) for n in nodes])
        U_all.append([col in nodes for col in vars['U'].columns])
    
    @mc.potential(name='covariate_constraint_%s'%name)
    def covariate_constraint(mu=vars['mu_age'], alpha=vars['alpha'], beta=vars['beta'],
                             U_all=U_all,
                             X_max=X_max,
                             X_min=X_min,
                             lower=pl.log(model.parameters[name]['level_bounds']['lower']),
                             upper=pl.log(model.parameters[name]['level_bounds']['upper'])):
        log_mu_max = pl.log(mu.max())
        log_mu_min = pl.log(mu.min())

        alpha = pl.array(alpha)
        if len(alpha) > 0:
            log_mu_max += max(alpha[U_all[1]]) + max(alpha[U_all[2]]) + max(alpha[U_all[3]])
            log_mu_min += min(alpha[U_all[1]]) + min(alpha[U_all[2]]) + min(alpha[U_all[3]])

        if len(beta) > 0:
            log_mu_max += pl.sum(pl.maximum(X_max*beta, X_min*beta))
            log_mu_min += pl.sum(pl.minimum(X_max*beta, X_min*beta))

        lower_violation = min(0., log_mu_min - lower)
        upper_violation = max(0., log_mu_max - upper)

        return mc.normal_like([lower_violation, upper_violation], 0., 1.e-6**-2)
    
    return dict(covariate_constraint=covariate_constraint)

    


def derivative_constraints(name, parameters, mu_age, ages):
    """ Generate PyMC objects implementing priors on the value of the rate function

    Parameters
    ----------
    name : str
    parameters : dict
    mu_age : pymc.Node with values of PCGP
    ages : array

    Results
    -------
    Returns dict of PyMC objects, including 'mu_age_derivative_potential'
    """
    if 'increasing' not in parameters or 'decreasing' not in parameters:
        return {}

    @mc.potential(name='mu_age_derivative_potential_%s'%name)
    def mu_age_derivative_potential(mu_age=mu_age,
                                    increasing_a0=pl.clip(parameters['increasing']['age_start']-ages[0], 0, len(ages)),
                                    increasing_a1=pl.clip(parameters['increasing']['age_end']-ages[0], 0, len(ages)),
                                    decreasing_a0=pl.clip(parameters['decreasing']['age_start']-ages[0], 0, len(ages)),
                                    decreasing_a1=pl.clip(parameters['decreasing']['age_end']-ages[0], 0, len(ages))):
        mu_prime = pl.diff(mu_age)
        inc_violation = mu_prime[increasing_a0:increasing_a1].clip(-1., 0.).sum()
        dec_violation = mu_prime[decreasing_a0:decreasing_a1].clip(0., 1.).sum()
        return mc.normal_like([inc_violation, dec_violation], 0., 1.e-6**-2)

    return dict(mu_age_derivative_potential=mu_age_derivative_potential)

