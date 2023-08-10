echo "Creating Python environment"
python3.10 -m venv env
source env/bin/activate

echo "Installing requirements"
pip3.10 install -r requirements.txt

echo "Adding pth file to env"
echo "$PWD/src" > env/lib/python3.10/site-packages/solar-potential.pth