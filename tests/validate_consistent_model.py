""" Validate Consistent Model
"""

# matplotlib will open windows during testing unless you do the following
import matplotlib
matplotlib.use("AGG")

# add to path, to make importing possible
import sys
sys.path += ['.', '..']

import pylab as pl
import pymc as mc

import data
import consistent_model
import fit_model
import graphics
import data_simulation
import pandas

reload(consistent_model)
reload(data_simulation)
reload(graphics)

pl.seterr('ignore')

def quadratic(a):
    return 1e-6 * (a * (100. - a) + 100.)

def constant(a):
    return .2 * pl.ones_like(a)

def validate_consistent_model_sim(N=500, delta_true=.5,
                                       true=dict(i=quadratic, f=constant, r=constant)):
    types = pl.array(['i', 'r', 'f', 'p'])

    ## generate simulated data
    model = data_simulation.simple_model(N)
    model.input_data['effective_sample_size'] = 1.
    model.input_data['value'] = 0.

    for t in types:
        model.parameters[t]['parameter_age_mesh'] = range(0, 101, 20)

    sim = consistent_model.consistent_model(model, 'all', 'total', 'all', {})
    for t in 'irf':
        for i, k_i in enumerate(sim[t]['knots']):
            sim[t]['gamma'][i].value = pl.log(true[t](k_i))

    age_start = pl.array(mc.runiform(0, 100, size=N), dtype=int)
    age_end = pl.array(mc.runiform(age_start, 100, size=N), dtype=int)

    data_type = types[mc.rcategorical(pl.ones(len(types), dtype=float) / float(len(types)), size=N)]

    a = pl.arange(101)
    age_weights = pl.ones_like(a)
    sum_wt = pl.cumsum(age_weights)

    p = pl.zeros(N)
    for t in types:
        mu_t = sim[t]['mu_age'].value
        sum_mu_wt = pl.cumsum(mu_t*age_weights)
    
        p_t = (sum_mu_wt[age_end] - sum_mu_wt[age_start]) / (sum_wt[age_end] - sum_wt[age_start])

        # correct cases where age_start == age_end
        i = age_start == age_end
        if pl.any(i):
            p_t[i] = mu_t[age_start[i]]

        # copy part into p
        p[data_type==t] = p_t[data_type==t]
    n = mc.runiform(100, 10000, size=N)

    model.input_data['data_type'] = data_type
    model.input_data['age_start'] = age_start
    model.input_data['age_end'] = age_end
    model.input_data['effective_sample_size'] = n
    model.input_data['true'] = p
    model.input_data['value'] = mc.rnegative_binomial(n*p, delta_true*n*p) / n

    # coarse knot spacing for fast testing
    for t in types:
        model.parameters[t]['parameter_age_mesh'] = range(0, 101, 20)

    ## Then fit the model and compare the estimates to the truth
    model.vars = {}
    model.vars = consistent_model.consistent_model(model, 'all', 'total', 'all', {})
    model.map, model.mcmc = fit_model.fit_consistent_model(model.vars, iter=10000, burn=5000, thin=25, tune_interval=100)

    graphics.plot_convergence_diag(model.vars)

    graphics.plot_fit(model, model.vars, {}, {})
    for i, t in enumerate('i r f p rr pf'.split()):
        pl.subplot(2, 3, i+1)
        pl.plot(a, sim[t]['mu_age'].value, 'w-', label='Truth', linewidth=2)
        pl.plot(a, sim[t]['mu_age'].value, 'r-', label='Truth', linewidth=1)

    #graphics.plot_one_type(model, model.vars['p'], {}, 'p')
    #pl.legend(fancybox=True, shadow=True, loc='upper left')

    pl.show()

    model.input_data['mu_pred'] = 0.
    model.input_data['sigma_pred'] = 0.
    for t in types:
        model.input_data['mu_pred'][data_type==t] = model.vars[t]['p_pred'].stats()['mean']
        model.input_data['sigma_pred'][data_type==t] = model.vars['p']['p_pred'].stats()['standard deviation']
    data_simulation.add_quality_metrics(model.input_data)

    model.delta = pandas.DataFrame(dict(true=[delta_true for t in types if t != 'rr']))
    model.delta['mu_pred'] = [pl.exp(model.vars[t]['eta'].trace()).mean() for t in types if t != 'rr']
    model.delta['sigma_pred'] = [pl.exp(model.vars[t]['eta'].trace()).std() for t in types if t != 'rr']
    data_simulation.add_quality_metrics(model.delta)

    print 'delta'
    print model.delta

    print '\ndata prediction bias: %.5f, MARE: %.3f, coverage: %.2f' % (model.input_data['abs_err'].mean(),
                                                     pl.median(pl.absolute(model.input_data['rel_err'].dropna())),
                                                                       model.input_data['covered?'].mean())

    model.mu = pandas.DataFrame()
    for t in types:
        model.mu = model.mu.append(pandas.DataFrame(dict(true=sim[t]['mu_age'].value,
                                                         mu_pred=model.vars[t]['mu_age'].stats()['mean'],
                                                         sigma_pred=model.vars[t]['mu_age'].stats()['standard deviation'])),
                                   ignore_index=True)
    data_simulation.add_quality_metrics(model.mu)
    print '\nparam prediction bias: %.5f, MARE: %.3f, coverage: %.2f' % (model.mu['abs_err'].mean(),
                                                                         pl.median(pl.absolute(model.mu['rel_err'].dropna())),
                                                                         model.mu['covered?'].mean())
    print


    data_simulation.initialize_results(model)
    data_simulation.add_to_results(model, 'delta')
    data_simulation.add_to_results(model, 'mu')
    data_simulation.add_to_results(model, 'input_data')
    data_simulation.finalize_results(model)

    print model.results

    return model


if __name__ == '__main__':
    model = validate_consistent_model_sim()
