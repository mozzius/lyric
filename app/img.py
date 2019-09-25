from PIL import Image


def thubnailify(name, ext, imgPath, savePath):
    img = Image.open(imgPath + "/" + name + "." + ext)
    square = cropToSquare(img)
    square.thumbnail((128, 128))
    square.save(savePath + "/" + name + ".png", quality=80)


def cropToSquare(img):
    width, height = img.size
    crop = min(img.size)
    return img.crop(
        (
            (width - crop) // 2,
            (height - crop) // 2,
            (width + crop) // 2,
            (height + crop) // 2,
        )
    )

