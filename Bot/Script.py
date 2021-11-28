##

import os

import cv2  
import numpy as np
from PIL import Image


class Script:

    script = {}
    device = None

    def __init__(file):
        pass


    def parse(self, file):

        bloc = "NONE"

        with open(file, 'r') as sfile:

            for line in sfile:
                ln = line.strip()
                # Skip empty line
                if len(ln) == 0:
                    continue
                # Skip comment
                if ln[0] == '#':
                    continue

                # If bloc line
                if ln[-1] == ':':
                    bloc = ln[:-1]

                    # Create new bloc
                    if not bloc in self.script:
                        self.script[bloc] = {'vars' : [], 'cmds' : []}
                    continue

                # Append command to bloc
                self.parseCommand(bloc, ln)
        
        return 0


    def parseCommand(self, bloc, cmd):
        args = cmd.split()
        if args[0].upper() == 'SET':
            vname = args[1]
            self.script[bloc]['vars'].append(cmd)
        else:
            self.script[bloc]['cmds'].append(cmd)
        return 0


    def run_on(self, device):
        self.device = device

        cb1 = self.load_anchor('Games/SoS/Marks/closebox_1.png')
        scr = self.refresh_screen()

        cbc = self.find_anchor(scr, cb1)
        self.click(cbc)


    def click(self, bbox):
        print('click within bbox', bbox)
        (x1, y1, x2, y2) = bbox
        self.device.touch(round((x1+x2)/2), round((y1+y2)/2))
        pass


    def load_anchor(self, sample_file):
        return cv2.imread(sample_file)

    
    def refresh_screen(self):
        screen = self.device.takeScreenshot()
        return self._cvt_image_to_cv2(screen)


    def find_anchor(self, screen, anchor) -> tuple:

        method = cv2.TM_SQDIFF_NORMED
        result = cv2.matchTemplate(anchor, screen, method)

        # We want the minimum squared difference
        mn,_,mnLoc,_ = cv2.minMaxLoc(result)

        # Extract the coordinates of our best match
        MPx,MPy = mnLoc

        # Get the size of the template. This is the same size as the match.
        trows,tcols = anchor.shape[:2]

        # Return found rectangle 
        return (MPx, MPy, MPx+tcols, MPy+trows)


    '''
        image = device.takeScreenshot()
        base_image = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)
        cv2.imshow('source', base_image)
        cv2.waitKey(0)

        template = cv2.imread("Games/SoS/Marks/closebox_1.png")  
        cv2.imshow('template', template)
        cv2.waitKey(0)

        method = cv2.TM_SQDIFF_NORMED

        result = cv2.matchTemplate(template, base_image, method)

        # We want the minimum squared difference
        mn,_,mnLoc,_ = cv2.minMaxLoc(result)

        # Draw the rectangle:
        # Extract the coordinates of our best match
        MPx,MPy = mnLoc

        # Step 2: Get the size of the template. This is the same size as the match.
        trows,tcols = template.shape[:2]

        # Step 3: Draw the rectangle on large_image
        cv2.rectangle(base_image, (MPx, MPy), (MPx + tcols, MPy + trows), (0,0,255), 2)

    '''


    def _cvt_cv2_to_image(self, img: np.ndarray) -> Image:
        return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


    def _cvt_image_to_cv2(self, img: Image) -> np.ndarray:
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


    def print(self):
        pass

