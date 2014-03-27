JCM="/opt/jcm"

if [ ${USER} != "root" ]; then
    echo "are you root ?"
    exit
fi


apt-get install -q python-vte

desktop-file-install jcm.desktop || exit -1

rm -rf ${JCM} || exit -1
mkdir ${JCM} || exit -1
cp -r main.py Frame.py example res plugins ${JCM} || exit -1
chmod 755 ${JCM} -R

