# This is a CSC 480 Project with Professor Rodrigo Canaan for the Summer 2024 2nd 5 Week Session. 

Team Member Names: Luke Zhuang, Kylie O'Donnell, Nitin Srinivasa, Charlie Ray, Jasmine Shouse

# This project is based on the GDMC 2024 Competition and builds upon the GDMC 2024 submission "Last Minute". 

Their project repo is: https://github.com/Xeon0X/GDMC-2024

# To run this code

You need to first have Forge installed and install the GDMC HTTP Interface mod. A good tutorial if needing help is this youtube video: https://www.youtube.com/watch?v=e1ydZA4qfSs&t=2066s&pp=ygUKZ2RtYyBodHRwIA%3D%3D

## Instructions to Run (Brought to you by the "Last Minute" github repo:
A procedural city generator for Minecraft as part of the GDMC 2024 competition. 

## Run

Install required packages using `pip`:
```bash
pip install -r requirements.txt
```

Run `main.py`.

## Dev 

First, setup your virtual environment using Python's built-in venv.

Install `pipreqs`:
```bash
pip install pipreqs
```

Run `pipreqs --ignore .venv --force` to generate an updated list of dependencies for the project in requirements file. Note that you should then change `skimage==...` by `scikit-image==0.23.2`.
