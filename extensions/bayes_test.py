#%% start
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  4 10:47:08 2023

@author: S.C.Azizabadi
"""

#\envs\pymc_env

from scipy import stats
import arviz as az
import numpy as np
import matplotlib.pyplot as plt
import pymc as pm
import seaborn as sns
import pandas as pd
#from theano import shared
from sklearn import preprocessing
print('Running on PyMC3 v{}'.format(pm.__version__))
data = pd.read_csv('renfe.csv')
data = data.sample(frac=0.01)
data.head(3)

#%% setup priors and liklihood and calc posterior
data['train_class'] = data['train_class'].fillna(data['train_class'].mode().iloc[0])
data['fare'] = data['fare'].fillna(data['fare'].mode().iloc[0])
data['price'] = data.groupby('fare').transform(lambda x: x.fillna(x.mean()))
#data = data[~data.price.isna()].copy()

az.plot_kde(data['price'].values, rug=True)
plt.yticks([0], alpha=0)

with pm.Model() as model_g:
    m = pm.Uniform('m', lower=0, upper=300)
    s = pm.HalfNormal('s', sigma=10)
    y = pm.Normal('y', mu=m, sigma=s, observed=data['price'].values)
    trace_g = pm.sample(1000, tune=1000, chains = 1)
    
#%% Plot   
az.plot_trace(trace_g)
trace_g.posterior['m'][0]


az.plot_pair(trace_g, kind='kde') 

az.summary(trace_g)



with model_g:
    trace_g.extend(pm.sample_posterior_predictive(trace_g))


fig, ax = plt.subplots()
az.plot_ppc(trace_g, ax=ax,num_pp_samples = 100)
ax.axvline(data['price'].mean(), ls="--", color="r", label="True mean")
ax.legend(fontsize=10);






_, ax = plt.subplots(figsize=(10, 5))
ax.hist([y.mean() for y in trace_g.posterior_predictive.y[0]])
ax.axvline(data.price.mean(), color = 'red')
ax.set(title='Posterior predictive of the mean', xlabel='mean(x)', ylabel='Frequency')


