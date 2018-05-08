#!/usr/bin/python


import sendmail
import io
import subprocess
import StringIO
import os
import time
from datetime import datetime
from PIL import Image

# 动作捕捉设置:
# Threshold          - 被记作改变的像素量改变量
# Sensitivity        - 在捕捉图像之前需要改变多少像素，如果有噪声的话，需要更高的像素。
# ForceCapture       - 是否强制在每次抓取时间秒内捕获图像
# filepath           - 照片保存的位置
# filenamePrefix     
# diskSpaceToReserve - 删除最旧图像以避免填充磁盘。在磁盘上留多少字节.
# cameraSettings     
threshold = 10
sensitivity = 20
forceCapture = True
forceCaptureTime = 60 * 60 # Once an hour
filepath = "/home/pi/picam"
filenamePrefix = "capture"
diskSpaceToReserve = 40 * 1024 * 1024 # Keep 40 mb free on disk
cameraSettings = ""

# 照片尺寸
saveWidth   = 1296
saveHeight  = 972
saveQuality = 15 # Set jpeg quality (0 to 100)

# 测试照片尺寸
testWidth = 100
testHeight = 75

# 默认设置
testAreaCount = 1
testBorders = [ [[1,testWidth],[1,testHeight]] ]  

debugMode = False 

# 捕捉一个测试图像
def captureTestImage(settings, width, height):
    command = "raspistill %s -w %s -h %s -t 200 -e bmp -n -o -" % (settings, width, height)
    imageData = StringIO.StringIO()
    imageData.write(subprocess.check_output(command, shell=True))
    imageData.seek(0)
    im = Image.open(imageData)
    buffer = im.load()
    imageData.close()
    return im, buffer

# 保存完整大小的图像 
def saveImage(settings, width, height, quality, diskSpaceToReserve):
    keepDiskSpaceFree(diskSpaceToReserve)
    time = datetime.now()
    filename = filepath + "/" + filenamePrefix + "-%04d%02d%02d-%02d%02d%02d.jpg" % (time.year, time.month, time.day, time.hour, time.minute, time.second)
    subprocess.call("raspistill %s -w %s -h %s -t 200 -e jpg -q %s -n -o %s" % (settings, width, height, quality, filename), shell=True)
    print ("Captured %s") % filename
    sendmail.send_email('1215628613@qq.com',filename)

# 磁盘上留多少位置
def keepDiskSpaceFree(bytesToReserve):
    if (getFreeSpace() < bytesToReserve):
        for filename in sorted(os.listdir(filepath + "/")):
            if filename.startswith(filenamePrefix) and filename.endswith(".jpg"):
                os.remove(filepath + "/" + filename)
                print ("Deleted %s/%s to avoid filling disk") % (filepath,filename)
                if (getFreeSpace() > bytesToReserve):
                    return

# 获取可用磁盘空间
def getFreeSpace():
    st = os.statvfs(filepath + "/")
    du = st.f_bavail * st.f_frsize
    return du

# 第一张
image1, buffer1 = captureTestImage(cameraSettings, testWidth, testHeight)

# 重置最后捕获时间
lastCapture = time.time()

for i in range(2):
    i  += 1

    # 获取比较图像 
    image2, buffer2 = captureTestImage(cameraSettings, testWidth, testHeight)

    # 计算改变的像素量
    changedPixels = 0
    takePicture = False

    if (debugMode): # 在调试模式下，保存具有标记的更改像素和可见的测试区域边界的位图文件。 
        debugimage = Image.new("RGB",(testWidth, testHeight))
        debugim = debugimage.load()

    for z in xrange(0, testAreaCount): # = xrange(0,1) with default-values = z will only have the value of 0 = only one scan-area = whole picture
        for x in xrange(testBorders[z][0][0]-1, testBorders[z][0][1]): # = xrange(0,100) with default-values
            for y in xrange(testBorders[z][1][0]-1, testBorders[z][1][1]):   # = xrange(0,75) with default-values; testBorders are NOT zero-based, buffer1[x,y] are zero-based (0,0 is top left of image, testWidth-1,testHeight-1 is botton right)
                if (debugMode):
                    debugim[x,y] = buffer2[x,y]
                    if ((x == testBorders[z][0][0]-1) or (x == testBorders[z][0][1]-1) or (y == testBorders[z][1][0]-1) or (y == testBorders[z][1][1]-1)):
                        # print "Border %s %s" % (x,y)
                        debugim[x,y] = (0, 0, 255) # 在调试模式下，将所有边界像素标记为蓝色。
                # 只检查绿色通道（最高质量的通道）
                pixdiff = abs(buffer1[x,y][1] - buffer2[x,y][1])
                if pixdiff > threshold:
                    changedPixels += 1
                    if (debugMode):
                        debugim[x,y] = (0, 255, 0) # 在调试模式下，将所有更改的像素标记为绿色。
                # 如果像素改变，保存图像 
                if (changedPixels > sensitivity):
                    takePicture = True # 稍后拍照
                if ((debugMode == False) and (changedPixels > sensitivity)):
                    break  
            if ((debugMode == False) and (changedPixels > sensitivity)):
                break  
        if ((debugMode == False) and (changedPixels > sensitivity)):
            break  

    if (debugMode):
        debugimage.save(filepath + "/debug.bmp") # 保存debug图片为bmp
        print ("debug.bmp saved, %s changed pixel") % changedPixels
    # else:
    #     print "%s changed pixel" % changedPixels

    if forceCapture:
        if time.time() - lastCapture > forceCaptureTime:
            takePicture = True

    if takePicture:
        lastCapture = time.time()
        saveImage(cameraSettings, saveWidth, saveHeight, saveQuality, diskSpaceToReserve)

    # 交换比较缓冲器
    image1 = image2
    buffer1 = buffer2
