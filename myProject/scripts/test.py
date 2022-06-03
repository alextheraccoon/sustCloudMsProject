import os
from PIL import Image

dirnames = []
dirpaths= []
filenames = []
filepaths = []
widths = []
heights = []
dpis = []
directory = 'tickets'
images_format = ["jpeg", "jpg", "png"]
small_paths = []
medium_paths = []
big_paths = []
size_smalls = []
size_mediums = []
size_bigs = []
dpis_small = []
dpis_medium = []
dpis_big = []
originals = []

# print(os.walk(directory))
for root, dirs, files in os.walk(directory):
#     print(len(dirs))
    for dirname in dirs:
        print(dirname)
        dirname_path = os.path.join(root, dirname)
        os.mkdir(dirname_path + "/im_small/")
        os.mkdir(dirname_path + "/im_medium/")
        os.mkdir(dirname_path + "/im_big/")
        for root_1, dirs_1, files_1 in os.walk(dirname_path):
            for filename in files_1:
                print(file_path)
                print(filename)
                if filename.split(".")[1].lower() in images_format:
                    file_path = dirname_path + "/" + filename
                    
                    size = 4961,7016
                    im = Image.open(file_path)
                    print(im.info['dpi'])
                    width, height = im.size
                    print(width)
                    print(height)
                    
                    pixel_diff = 200
                    if (width - pixel_diff) > 0 and (height - pixel_diff) > 0:
                        size_small = (width - pixel_diff), (height - pixel_diff)
                        im_small = im.resize(size_small, Image.ANTIALIAS)
                        im_small_name = dirname_path + "/im_small/" + filename
                        print(im_small_name)
                        im_small.save(im_small_name, "PNG")
                        size_big = (width + pixel_diff), (height + pixel_diff)
                        im_big = im.resize(size_big, Image.ANTIALIAS)
                        im_big_name = dirname_path + "/im_big/" + filename
                        print(im_big_name)
                        im_big.save(im_big_name, "PNG")
                        im_medium_name = dirname_path + "/im_medium/" + filename
                        size_medium = im.size
                        os.rename(file_path, im_medium_name)
                        im_medium = Image.open(im_medium_name)
                        original = 'medium'
                    else:
                        size_small = im.size
                        size_medium = (width + pixel_diff), (height + pixel_diff)
                        im_medium = im.resize(size_medium, Image.ANTIALIAS)
                        im_medium_name = dirname_path + "/im_medium/" + filename
                        print(im_medium_name)
                        im_medium.save(im_medium_name, "PNG")
                        size_big = (width + (pixel_diff * 2)), (height + (pixel_diff * 2))
                        im_big = im.resize(size_big, Image.ANTIALIAS)
                        im_big_name = dirname_path + "/im_big/" + filename
                        print(im_big_name)
                        im_big.save(im_big_name, "PNG")
                        im_small_name = dirname_path + "/im_small/" + filename
                        os.rename(file_path, im_small_name)
                        im_small = Image.open(im_small_name)
                        original = 'small'
                    
                    width, height = im.size
                    dirnames.append(dirname)
                    dirpaths.append(dirname_path)
                    filenames.append(filename)
                    small_paths.append(im_small_name)
                    medium_paths.append(im_medium_name)
                    big_paths.append(im_big_name)
                    size_smalls.append(size_small)
                    size_mediums.append(size_medium)
                    size_bigs.append(size_big)
                    originals.append(original)
#                     filepaths.append(file_path)
#                     widths.append(width)
#                     heights.append(height)
                    if 'dpi' in im_small.info:
                        dpis_small.append(im_small.info['dpi'])
                    else:
                        dpis_small.append((0,0))
                    if 'dpi' in im_medium.info:
                        dpis_medium.append(im_medium.info['dpi'])
                    else:
                        dpis_medium.append((0,0))
                    if 'dpi' in im_big.info:
                        dpis_big.append(im_big.info['dpi'])
                    else:
                        dpis_big.append((0,0))
            
            break
    break
        