from pdf2image import convert_from_bytes

def main():
    f = open("resume.pdf", "rb")
    infile = f.read()
    f.close()
    images = convert_from_bytes(infile)
    for idx, img in enumerate(images):
        img.save(f"{idx}.jpg", "jpeg")
if __name__ == "__main__":
    main()