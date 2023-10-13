#!/bin/bash
echo "source $CONDA_PREFIX/etc/profile.d/conda.sh"
source $CONDA_PREFIX/etc/profile.d/conda.sh
name=flask

echo "install environment $name"
conda create -y --force -n $name

echo "install packages"
conda install -y -n $name -c anaconda "python>=3.9.6"
conda install -y -n $name -c anaconda numpy
conda install -y -n $name -c anaconda pandas
conda install -y -n $name -c anaconda flask
conda install -y -n $name -c anaconda ipykernel
conda install -y -n $name -c anaconda scikit-learn
conda install -y -n $name -c anaconda seaborn
conda install -y -n $name -c conda-forge matplotlib
conda install -y -n $name -c conda-forge flask-sqlalchemy
conda install -y -n $name -c conda-forge opencv
conda install -y -n $name -c conda-forge sortedcontainers


