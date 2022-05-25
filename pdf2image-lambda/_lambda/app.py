import os
import boto3
import json
import uuid
import logging
import tempfile
from io import BytesIO

from chalice import Chalice
from pdf2image import convert_from_bytes


app = Chalice(app_name="_pdf2image")

# Setup logging for debugging purposes
app.log.setLevel(logging.DEBUG)

# Load the environment variables
DPI = 300
if "DPI" in os.environ:
    try:
        DPI = int(os.environ["DPI"])
    except Exception as e:
        app.log.debug(
            f"Couldn't process DPI environment variable: {str(e)}.  Using the default: DPI=300"
        )
else:
    app.log.info(f"No DPI environment variable set.  Using the default: DPI=300")

FMT = "jpeg"
if "FMT" in os.environ:
    try:
        FMT = str(os.environ["FMT"])
    except Exception as e:
        app.log.debug(
            f"Couldn't process FMT environment variable: {str(e)}.  Using the default: FMT=jpeg"
        )
else:
    app.log.info(f"No FMT environment variable set.  Using the default: FMT=jpeg")

DEST_BUCKET = ""
if "DEST_BUCKET" in os.environ:
    DEST_BUCKET = str(os.environ["DEST_BUCKET"])
    app.log.info(f"Setting the destination bucket: {DEST_BUCKET}")
else:
    app.log.debug(f"Couldn't process the DEST_BUCKET environment variable. ")

ORIGIN_BUCKET = ""
if "ORIGIN_BUCKET" in os.environ:
    ORIGIN_BUCKET = str(os.environ["ORIGIN_BUCKET"])
    app.log.info(f"Setting the origin bucket: {ORIGIN_BUCKET}. ")
else:
    app.log.debug(f"Couldn't process the ORIGIN_BUCKET environment variable. ")

REGION = ""
if "REGION" in os.environ:
    try:
        REGION = str(os.environ["REGION"])
    except Exception as e:
        app.log.debug(f"Couldn't process REGION environment variable: {str(e)}.")
else:
    app.log.info(
        f"No REGION environment variable set.  Using the default: REGION=ap-south-1"
    )

# Function to upload images to S3
def upload_to_s3(pdf_key_name, image_key_name, image, page_num, size):
    # Save the image into the buffer
    buffer = BytesIO()
    image.save(buffer, FMT.upper())
    buffer.seek(0)
    app.log.info(
        f"Saving page number {str(page_num)} to S3 at location: {DEST_BUCKET}, {image_key_name}."
    )

    # Upload the image to S3 Bucket
    # Add the relevant metadata
    s3 = boto3.resource("s3")
    s3.Object(DEST_BUCKET, image_key_name).put(
        Body=buffer,
        Metadata={
            "ORIGINAL_DOCUMENT_BUCKET": ORIGIN_BUCKET,
            "ORIGINAL_DOCUMENT_KEY": pdf_key_name,
            "PAGE_NUMBER": str(page_num),
            "PAGE_COUNT": str(size),
        },
    )

    # Prepare saved image url
    object_url = "https://%s.s3.%s.amazonaws.com/%s" % (
        DEST_BUCKET,
        REGION,
        image_key_name,
    )
    app.log.info(f"URL => {object_url}")

    return object_url


# The index function is the main function that will be executed by lambda
@app.route("/{value}", methods=['GET'])
def index(value):
    # KEY stores the name of the PDF you would like to convert
    KEY = value

    # Retreive PDF file from S3
    app.log.info(f"Retrieving {KEY} ...")
    s3 = boto3.resource("s3")
    obj = s3.Object(ORIGIN_BUCKET, KEY)
    infile = obj.get()["Body"].read()
    pdf_file_bytes = bytes(infile)

    app.log.info(f"Successfully retrieved S3 object {KEY}.")

    # Start converting PDF into JPEG Images
    app.log.info("Converting PDF to images!")

    # Here we are using temp directory because it makes the whole process faster and error free.
    # We are passing some parameters to the convert_from_bytes function,
    # you can learn about them on the official github repo of pdf2image
    images = None
    with tempfile.TemporaryDirectory() as path:
        images = convert_from_bytes(
            pdf_file_bytes,
            dpi=300,
            fmt=FMT,
            thread_count=8,
            output_folder=path,
            jpegopt={"quality": 100, "optimize": False, "progressive": False},
            poppler_path="/var/task/lib/poppler_binaries/",
        )

    app.log.info("Images are ready!")

    # Iterate over the images list and save them on S3 bucket one by one.
    size = len(images)
    result = []
    DIR_ID = uuid.uuid4()
    for page_num, image in enumerate(images):
        # Creating the name of image is necessary
        image_key_name = "imagesFromPDF/{0}/{1}/{2}{3}".format(KEY, DIR_ID, str(page_num), "." + FMT)
        url = upload_to_s3(KEY, image_key_name, image, page_num, size)
        result.append(url)
	# Prepare the JSON with the URLs of the uploaded images.
    payload = json.dumps({"images": result})
    custom_headers = {
        "Content-Type": "application/json",
    }

    app.log.info("images uploaded!")
    app.log.info(payload)

    return payload