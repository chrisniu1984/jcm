#!/bin/bash

JCM="/opt/jcm"

if [ ${USER} != "root" ]; then
    echo "are you root ?"
    exit
fi

rm -rf ${JCM} || exit -1
mkdir ${JCM} || exit -1

cp -r main.py NIU res plugins ${JCM} || exit -1
chmod 755 ${JCM}/main.py -R

