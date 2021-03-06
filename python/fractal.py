from numpy import random, arange
from PIL import Image

common = {
	"dragon-curve" : ([(0.5, -0.5, 0, 0.5, 0.5, 0), (0.5, -0.5, 1, 0.5, 0.5, 0)], None), \
	"barnsley-fern" : ([(0, 0, 0, 0, .16, 0), (.85, .04, 0, -0.04, .85, 1.6), \
		(0.2, -0.26, 0, 0.23, 0.22, 1.6), (-0.15, 0.28, 0, 0.26, 0.24, 0.44)], \
		(.01, .85, .07, .07))
}

def getFractalSeries(n, transform, probabilities=None):
	x = 0.0
	y = 0.0
	xValues, yValues = [x], [y]
	rand = []
	if probabilities is None:
		rand = random.choice(arange(len(transform)), size=n)
	else:
		rand = random.choice(arange(len(transform)), size=n, p=probabilities)

	for i in range (n):
		r = rand[i]
		
		x2 = x*transform[r][0] + y*transform[r][1] + transform[r][2]
		xValues.append(x2)
		
		y2 = x*transform[r][3] + y*transform[r][4] + transform[r][5]
		yValues.append(y2)
		
		x = x2
		y = y2
	
	return xValues, yValues
	
def makeImage(name, xValues, yValues, width=1920, height=1080):
	width -= 1
	height -= 1
	maxX, maxY = max(xValues), max(yValues)
	minX, minY = min(xValues), min(yValues)
	
	xSize = maxX - minX
	ySize = maxY - minY
	
	maxRatio = max(xSize / width, ySize / height)
	xOffset = int(width - xSize/maxRatio) // 2
	yOffset = int(height - ySize/maxRatio) // 2

	img = Image.new('RGB', (width+1, height+1), "black") # create a new black image
	pixels = img.load() # create the pixel map
	
	xColor = 255/width
	yColor = 255/height
	zColor = 255/(width*height)
	
	for i in range(len(xValues)):
		x = int((xValues[i]-minX)/maxRatio) + xOffset
		y = int((yValues[i]-minY)/maxRatio) + yOffset
		pixels[x, y] = int(x*xColor), int(y*yColor), int((x*y)*zColor)

	img.show()
	img.save(name + ".png")

name = "dragon-curve"
xValues, yValues = getFractalSeries(500000, *common[name])
makeImage(name, xValues, yValues)
