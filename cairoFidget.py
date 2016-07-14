#!/usr/bin/python2

##
# This file is part of pyFidget, licensed under the MIT License (MIT).
#
# Copyright (c) 2016 Wolf480pl <wolf480@interia.pl>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
##

import fidget
import cairoEng
import os

if __name__ == "__main__":
		spritefilename = 'fidget-sprites.png'
		#if user is running windows then make sure python knows the exact folder where the sprite file is
		#which by default is the script's folder, otherwise python can't see the file in windows
		if os.name=="nt":
				spritefilename = os.path.dirname(__file__) + "\\" + 'fidget-sprites.png'
		cairoEng.run(fidget.Fidget(), spritefilename, fidget.getFrameRect, (171, 151), (-28, -2))
