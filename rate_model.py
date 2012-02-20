""" Several rate models"""

import pylab as pl
import pymc as mc


def binom(name, pi, p, n):
    """ Generate PyMC objects for a binomial model

    Parameters
    ----------
    name : str
    pi : pymc.Node, expected values of rates
    p : array, observed values of rates
    n : array, effective sample sizes of rates

    Results
    -------
    Returns dict of PyMC objects, including 'p_obs' and 'p_pred'
    the observed stochastic likelihood and data predicted stochastic
    """
    assert pl.all(p >= 0), 'observed values must be non-negative'
    assert pl.all(n >= 0), 'effective sample size must non-negative'

    @mc.observed(name='p_obs_%s'%name)
    def p_obs(value=p, pi=pi, n=n):
        return mc.binomial_like(value*n, n, pi)

    # for any observation with n=0, make predictions for n=1.e10, to use for predictive validity
    n_nonzero = pl.array(n.copy(), dtype=int)
    n_nonzero[n==0] = 1e10
    @mc.deterministic(name='p_pred_%s'%name)
    def p_pred(pi=pi, n=n_nonzero):
        return mc.rbinomial(n, pi) / (1.*n)

    return dict(p_obs=p_obs, p_pred=p_pred)


def beta_binom(name, pi, p, n):
    """ Generate PyMC objects for a beta-binomial model

    Parameters
    ----------
    name : str
    pi : pymc.Node, expected values of rates
    p : array, observed values of rates
    n : array, effective sample sizes of rates

    Results
    -------
    Returns dict of PyMC objects, including 'p_obs' and 'p_pred'
    the observed stochastic likelihood and data predicted stochastic
    """
    assert pl.all(p >= 0), 'observed values must be non-negative'
    assert pl.all(n >= 0), 'effective sample size must non-negative'


    p_alpha = mc.Uninformative('p_alpha_%s'%name, value=1.)
    @mc.deterministic(name='p_beta_%s'%name)
    def p_beta(p_alpha=p_alpha, pi=pi):
        return p_alpha * (1-pi) / pi

    pi_latent = [mc.Beta('pi_latent_%s_%d'%(name,i), p_alpha, p_beta[i], value=pi_i) for i, pi_i in enumerate(pi.value)]

    @mc.observed(name='p_obs_%s'%name)
    def p_obs(value=p, pi=pi_latent, n=n):
        return mc.binomial_like(value*n, n, pi)

    # for any observation with n=0, make predictions for n=1.e10, to use for predictive validity
    n_nonzero = pl.array(n.copy(), dtype=int)
    n_nonzero[n==0] = 1e10
    @mc.deterministic(name='p_pred_%s'%name)
    def p_pred(pi=pi_latent, n=n_nonzero):
        return mc.rbinomial(n, pi) / (1.*n)

    return dict(p_alpha=p_alpha, p_beta=p_beta, pi_latent=pi_latent, p_obs=p_obs, p_pred=p_pred)


def poisson(name, pi, p, n):
    """ Generate PyMC objects for a poisson model

    Parameters
    ----------
    name : str
    pi : pymc.Node, expected values of rates
    p : array, observed values of rates
    n : array, effective sample sizes of rates

    Results
    -------
    Returns dict of PyMC objects, including 'p_obs' and 'p_pred'
    the observed stochastic likelihood and data predicted stochastic
    """
    assert pl.all(p >= 0), 'observed values must be non-negative'
    assert pl.all(n >= 0), 'effective sample size must non-negative'

    @mc.observed(name='p_obs_%s'%name)
    def p_obs(value=p, pi=pi, n=n):
        return mc.poisson_like(value*n, (pi*n).clip(1.e-9,pl.inf))

    # for any observation with n=0, make predictions for n=1.e10, to use for predictive validity
    n_nonzero = pl.array(n.copy(), dtype=float)
    n_nonzero[n==0.] = 1.e10
    @mc.deterministic(name='p_pred_%s'%name)
    def p_pred(pi=pi, n=n_nonzero):
        return mc.rpoisson((pi*n).clip(1.e-9, pl.inf)) / (1.*n)

    return dict(p_obs=p_obs, p_pred=p_pred)


def neg_binom(name, pi, delta, p, n):
    """ Generate PyMC objects for a negative binomial model

    Parameters
    ----------
    name : str
    pi : pymc.Node, expected values of rates
    delta : pymc.Node, dispersion parameters of rates
    p : array, observed values of rates
    n : array, effective sample sizes of rates

    Results
    -------
    Returns dict of PyMC objects, including 'p_obs' and 'p_pred'
    the observed stochastic likelihood and data predicted stochastic
    """
    assert pl.all(p >= 0), 'observed values must be non-negative'
    assert pl.all(n >= 0), 'effective sample size must non-negative'

    @mc.observed(name='p_obs_%s'%name)
    def p_obs(value=p, pi=pi, delta=delta, n=n):
        return mc.negative_binomial_like(value*n, pi*n+1.e-9, delta)

    # for any observation with n=0, make predictions for n=1.e9, to use for predictive validity
    n_nonzero = n.copy()
    n_nonzero[n==0.] = 1.e9
    @mc.deterministic(name='p_pred_%s'%name)
    def p_pred(pi=pi, delta=delta, n=n_nonzero):
        return mc.rnegative_binomial(pi*n+1.e-9, delta) / pl.array(n+1.e-9, dtype=float)

    return dict(p_obs=p_obs, p_pred=p_pred)

# TODO: remove this legacy-named method
neg_binom_model = neg_binom

def neg_binom_lower_bound_model(name, pi, delta, p, n):
    """ Generate PyMC objects for a negative binomial lower bound model

    Parameters
    ----------
    name : str
    pi : pymc.Node, expected values of rates
    delta : pymc.Node, dispersion parameters of rates
    p : array, observed values of rates
    n : array, effective sample sizes of rates

    Results
    -------
    Returns dict of PyMC objects, including 'p_obs' the observed
    stochastic likelihood
    """
    assert pl.all(p >= 0), 'observed values must be non-negative'
    assert pl.all(n > 0), 'effective sample size must be positive'

    @mc.observed(name='p_obs_%s'%name)
    def p_obs(value=p, pi=pi, delta=delta, n=n):
        return mc.negative_binomial_like(pl.maximum(value*n, pi*n), pi*n+1.e-9, delta)

    return dict(p_obs=p_obs)


def normal_model(name, pi, sigma, p, s):
    """ Generate PyMC objects for a normal model

    Parameters
    ----------
    name : str
    pi : pymc.Node, expected values of rates
    sigma : pymc.Node, dispersion parameters of rates
    p : array, observed values of rates
    s : array, standard error of rates

    Results
    -------
    Returns dict of PyMC objects, including 'p_obs' and 'p_pred'
    the observed stochastic likelihood and data predicted stochastic
    """
    assert pl.all(s >= 0), 'standard error must be non-negative'

    i_inf = pl.isinf(s)
    @mc.observed(name='p_obs_%s'%name)
    def p_obs(value=p, pi=pi, sigma=sigma, s=s):
        return mc.normal_like(p[~i_inf], pi[~i_inf], 1./(sigma**2. + s[~i_inf]**2.))

    s_noninf = s.copy()
    s_noninf[i_inf] = 0.    
    @mc.deterministic(name='p_pred_%s'%name)
    def p_pred(pi=pi, sigma=sigma, s=s_noninf):
        return mc.rnormal(pi, 1./(sigma**2. + s**2.))

    return dict(p_obs=p_obs, p_pred=p_pred)


def log_normal_model(name, pi, sigma, p, s):
    """ Generate PyMC objects for a log-normal model

    Parameters
    ----------
    name : str
    pi : pymc.Node, expected values of rates
    sigma : pymc.Node, dispersion parameters of rates
    p : array, observed values of rates
    s : array, standard error sizes of rates

    Results
    -------
    Returns dict of PyMC objects, including 'p_obs' and 'p_pred'
    the observed stochastic likelihood and data predicted stochastic
    """
    assert pl.all(p > 0), 'observed values must be positive'
    assert pl.all(s >= 0), 'standard error must be non-negative'

    i_inf = pl.isinf(s)
    @mc.observed(name='p_obs_%s'%name)
    def p_obs(value=p, pi=pi, sigma=sigma, s=s/p):
        return mc.normal_like(pl.log(p[~i_inf]), pl.log(pi[~i_inf]),
                              1./(sigma**2. + (s[~i_inf]/p[~i_inf])**2.))

    s_noninf = s.copy()
    s_noninf[i_inf] = 0.    
    @mc.deterministic(name='p_pred_%s'%name)
    def p_pred(pi=pi, sigma=sigma, s=s_noninf):
        return pl.exp(mc.rnormal(pl.log(pi), 1./(sigma**2. + (s/pi)**2)))

    return dict(p_obs=p_obs, p_pred=p_pred)


def offset_log_normal(name, pi, sigma, p, s):
    """ Generate PyMC objects for an offset log-normal model
    
    Parameters
    ----------
    name : str
    pi : pymc.Node, expected values of rates
    sigma : pymc.Node, dispersion parameters of rates
    p : array, observed values of rates
    s : array, standard error sizes of rates

    Results
    -------
    Returns dict of PyMC objects, including 'p_obs' and 'p_pred'
    the observed stochastic likelihood and data predicted stochastic
    """
    assert pl.all(p > 0), 'observed values must be positive'
    assert pl.all(s >= 0), 'standard error must be non-negative'

    p_zeta = mc.Uniform('p_zeta_%s'%name, 1.e-9, 10., value=1.e-6)

    i_inf = pl.isinf(s)
    @mc.observed(name='p_obs_%s'%name)
    def p_obs(value=p, pi=pi, sigma=sigma, s=s/p, p_zeta=p_zeta):
        return mc.normal_like(pl.log(p[~i_inf]+p_zeta), pl.log(pi[~i_inf]+p_zeta),
                              1./(sigma**2. + (s[~i_inf]/(p[~i_inf]+p_zeta))**2.))

    s_noninf = s.copy()
    s_noninf[i_inf] = 0.
    @mc.deterministic(name='p_pred_%s'%name)
    def p_pred(pi=pi, sigma=sigma, s=s_noninf, p_zeta=p_zeta):
        return pl.exp(mc.rnormal(pl.log(pi+p_zeta), 1./(sigma**2. + (s/(pi+p_zeta))**2)) - p_zeta)

    return dict(p_zeta=p_zeta, p_obs=p_obs, p_pred=p_pred)
