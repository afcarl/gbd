""" Functions for generating synthetic data

"""

from pylab import randn, dot, arange, zeros
from pymc import rmv_normal_cov, gp
import csv

def write(data, out_fname):
    """ write data.csv file"""
    fout = open(out_fname, 'w')
    csv.writer(fout).writerows(data)
    fout.close()

def countries_by_region():
    c4 = dict([[d[0], d[1:]] for d in csv.reader(open('../country_region.csv'))])
    c4.pop('World')
    return c4

def col_names():
    return [['region', 'country', 'year', 'y'] + ['x%d'%i for i in range(10)]]

def generate_fe(out_fname='data.csv'):
    """ replace data.csv with random data based on a fixed effects model

    This function generates data for all countries in all regions, based on the model::

        Y_r,c,t = beta . X_r,c,t + e_r,c,t
        e_r,c,t ~ N(0,1)

    """
    c4 = countries_by_region()

    data = col_names()
    beta = randn(10)
    for t in range(1990, 2005):
        for r in c4:
            for c in c4[r]:
                x = [1] + list(randn(9))
                y = float(dot(beta, x))
                data.append([r, c, t, y] + list(x))

    write(data, out_fname)


def generate_re(out_fname='data.csv'):
    """ replace data.csv with random data based on a random effects model

    This function generates data for all countries in all regions, based on the model::

        Y_r,c,t = (beta + u_r,c,t) * X_r,c,t + e_r,c,t
        u_r,c,t[k] ~ N(0,1)
        e_r,c,t ~ N(0,1)

        beta ~ N(0, 10^2)
        X_r,c,t[k] ~ N(0, 1) for k >= 1

    """
    c4 = countries_by_region()

    data = col_names()
    beta = 10.*randn(10)
    for t in range(1990, 2005):
        for r in c4:
            for c in c4[r]:
                x = [1] + list(randn(9))
                y = float(dot(beta+randn(10), x))
                data.append([r, c, t, y] + list(x))
    write(data, out_fname)


def generate_gp_re(out_fname='data.csv'):
    """ replace data.csv with random data based on a gaussian process random effects model

    This function generates data for all countries in all regions, based on the model::

        Y_r,c,t = beta * X_r,c,t + f_c(t) + e_r,c,t
        f_c ~ GP(0,C)
        e_r,c,t ~ N(0,1)

        X_r,c,t[k] ~ N(0, 1) for k >= 2

    """
    c4 = countries_by_region()

    data = col_names()
    beta = [10., -.5, .1, .1, -.1, 0., 0., 0., 0., 0.]
    for r in c4:
        for c in c4[r]:
            C_c = gp.matern.euclidean(arange(15), arange(15), amp=3., scale=20., diff_degree=2)
            f = rmv_normal_cov(zeros(15), C_c)
            
            for t in range(1990, 2005):
                x = [1] + [t-1990.] + list(randn(8))
                y = float(dot(beta, x)) + f[t-1990]
                data.append([r, c, t, y] + list(x))
    write(data, out_fname)


def generate_nre(out_fname='data.csv'):
    """ replace data.csv with random data based on a nested random effects model

    This function generates data for all countries in all regions, based on the model::

        Y_r,c,t = (beta + u_r + u_r,c,t) * X_r,c,t + e_r,c,t
        u_r[k] ~ N(0,2^2)
        u_r,c,t[k] ~ N(0,1)
        e_r,c,t ~ N(0,1)

        beta ~ N(0, 10^2)
        X_r,c,t[k] ~ N(0, 1) for k >= 1

    """
    c4 = countries_by_region()

    data = col_names()
    beta = 10.*randn(10)
    for t in range(1990, 2005):
        for r in c4:
            u_r = .2*randn(10)
            for c in c4[r]:
                x = [1] + list(randn(9))
                y = float(dot(beta + u_r + randn(10), x))
                data.append([r, c, t, y] + list(x))
    write(data, out_fname)

def knockout_uniformly_at_random(in_fname='noisy_data.csv', out_fname='missing_noisy_data.csv', pct=20.):
    """ replace data.csv y column with uniformly random missing entries

    Parameters
    ----------
    pct : float, percent to knockout
    """
    from pylab import csv2rec, rec2csv, nan, rand

    data = csv2rec(in_fname)
    for i, row in enumerate(data):
        if rand() < pct/100.:
            data[i].y = nan
    rec2csv(data, out_fname)

def add_sampling_error(in_fname='data.csv', out_fname='noisy_data.csv', std=1.):
    """ add normally distributed noise to data.csv y column

    Parameters
    ----------
    std : float, standard deviation of noise
    """
    from pylab import csv2rec, rec2csv, randn

    data = csv2rec(in_fname)
    for i, row in enumerate(data):
        data[i].y += std * randn(1)
    rec2csv(data, out_fname)


def test():
    generate_fe('test_data.csv')  # replace data.csv with file based on fixed-effects model
    generate_re('test_data.csv')
    generate_nre('test_data.csv')
    generate_gp_re('test_data.csv')

    # add normally distributed noise (with standard deviation 1.0) to test_data.y
    add_sampling_error('test_data.csv',
                       'noisy_test_data.csv',
                       std=1.)

    # replace new_data.csv by knocking out data uar from data.csv
    knockout_uniformly_at_random('noisy_test_data.csv',
                                 'missing_noisy_test_data.csv',
                                 pct=25.)
