from server_settings import *

# time to wait (in seconds) between checking the server for new jobs
SLEEP_SECS = 2.

# shell command string to spawn a fit process
GBD_FIT_STR = 'python2.5 gbd_fit.py %s %d'


# disease model parameters

NEARLY_ZERO = 1.e-10
MAX_AGE = 101

MISSING = -99

PRIOR_SEP_STR = ','

KEY_DELIM_CHAR = '+'

data_types = ['prevalence data',
              'incidence data',
              'remission data',
              'case-fatality data',
              'duration data',
              'all-cause mortality data',
              ]

output_data_types = ['Prevalence',
                     'Incidence',
                     'Remission',
                     'Case-fatality',
                     'Relative-risk',
                     'Duration',
                     'YLD']

stoch_var_types = output_data_types + ['bins']

gbd_regions = [u'Asia Pacific, High Income',
               u'Asia, Central',
               u'Asia, East',
               u'Asia, South',
               u'Asia, Southeast',
               u'Australasia',
               u'Caribbean',
               u'Europe, Central',
               u'Europe, Eastern',
               u'Europe, Western',
               u'Latin America, Andean',
               u'Latin America, Central',
               u'Latin America, Southern',
               u'Latin America, Tropical',
               u'North Africa/Middle East',
               u'North America, High Income',
               u'Oceania',
               u'Sub-Saharan Africa, Central',
               u'Sub-Saharan Africa, East',
               u'Sub-Saharan Africa, Southern',
               u'Sub-Saharan Africa, West']

gbd_years = [1990, 2005]

gbd_sexes = ['Male', 'Female']