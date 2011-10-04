""" Test covariate model

These tests are use randomized computation, so they might fail
occasionally due to stochastic variation
"""

# add to path, to make importing possible
import sys
sys.path += ['.', '..']

import pylab as pl
import pymc as mc
import networkx as nx
import pandas

import data
import data_simulation
import data_model
import rate_model
import age_pattern
import covariate_model
reload(covariate_model)
reload(data_model)

def test_covariate_model_sim_no_hierarchy():
    # simulate normal data
    hierarchy, output_template = data_simulation.small_output()

    X = mc.rnormal(0., 1.**2, size=(128,3))

    beta_true = [-.1, .1, .2]
    Y_true = pl.dot(X, beta_true)

    pi_true = pl.exp(Y_true)
    sigma_true = .01

    p = mc.rnormal(pi_true, 1./sigma_true**2.)

    data = pandas.DataFrame(dict(value=p, x_0=X[:,0], x_1=X[:,1], x_2=X[:,2]))
    data['area'] = 'all'
    data['sex'] = 'total'
    data['year_start'] = 2000
    data['year_end'] = 2000

    # create model and priors
    vars = {}
    vars.update(covariate_model.mean_covariate_model('test', 1, data, output_template, hierarchy, 'all', 'total', 'all'))
    vars.update(rate_model.normal_model('test', vars['pi'], 0., p, sigma_true))

    # fit model
    m = mc.MCMC(vars)
    m.sample(2)


def test_covariate_model_sim_w_hierarchy():
    n = 50

    # setup hierarchy
    hierarchy, output_template = data_simulation.small_output()

    # simulate normal data
    area_list = pl.array(['all', 'USA', 'CAN'])
    area = area_list[mc.rcategorical([.3, .3, .4], n)]

    sex_list = pl.array(['male', 'female', 'total'])
    sex = sex_list[mc.rcategorical([.3, .3, .4], n)]

    year = pl.array(mc.runiform(1990, 2010, n), dtype=int)
        
    alpha_true = dict(all=0., USA=.1, CAN=-.2)

    pi_true = pl.exp([alpha_true[a] for a in area])
    sigma_true = .05

    p = mc.rnormal(pi_true, 1./sigma_true**2.)

    data = pandas.DataFrame(dict(value=p, area=area, sex=sex, year_start=year, year_end=year))

    # create model and priors
    vars = {}
    vars.update(covariate_model.mean_covariate_model('test', 1, data, output_template, hierarchy,
                                                     'all', 'total', 'all'))
    vars.update(rate_model.normal_model('test', vars['pi'], 0., p, sigma_true))

    # fit model
    m = mc.MCMC(vars)
    m.sample(2)

def test_covariate_model_dispersion():
    # simulate normal data
    n = 100

    hierarchy, output_template = data_simulation.small_output()

    Z = mc.rcategorical([.5, 5.], n)
    zeta_true = -.2

    pi_true = .1
    ess = 10000
    eta_true = pl.log(50)
    delta_true = 50 + pl.exp(eta_true)

    p = mc.rnegative_binomial(pi_true*ess, delta_true*pl.exp(Z*zeta_true)) / float(ess)

    data = pandas.DataFrame(dict(value=p, z_0=Z))
    data['area'] = 'all'
    data['sex'] = 'total'
    data['year_start'] = 2000
    data['year_end'] = 2000

    # create model and priors
    vars = dict(mu=mc.Uninformative('mu_test', value=pi_true))
    vars.update(covariate_model.mean_covariate_model('test', vars['mu'], data, output_template, hierarchy, 'all', 'total', 'all'))
    vars.update(covariate_model.dispersion_covariate_model('test', data))
    vars.update(rate_model.neg_binom_model('test', vars['pi'], vars['delta'], p, ess))

    # fit model
    m = mc.MCMC(vars)
    m.sample(2)

def test_covariate_model_shift_for_root_consistency():
    # generate simulated data
    n = 50
    sigma_true = .025
    a = pl.arange(0, 100, 1)
    pi_age_true = .0001 * (a * (100. - a) + 100.)
    
    d = data.ModelData()
    d.input_data = data_simulation.simulated_age_intervals('p', n, a, pi_age_true, sigma_true)
    d.hierarchy, d.output_template = data_simulation.small_output()
    

    # create model and priors
    vars = data_model.data_model('test', d, 'p', 'all', 'total', 'all', None, None)

    vars = data_model.data_model('test', d, 'p', 'all', 'male', 1990, None, None)

    # fit model
    m = mc.MCMC(vars)
    m.use_step_method(mc.AdaptiveMetropolis, [m.gamma_bar, m.beta])
    m.use_step_method(mc.AdaptiveMetropolis, m.gamma[1:])

    m.sample(3)

    # check estimates
    pi_usa = covariate_model.predict_for(d.output_template, d.hierarchy, 'all', 'male', 1990, 'USA', 'male', 1990, vars)


if __name__ == '__main__':
    import nose
    nose.runmodule()
    
