import subprocess

from gutenberg2zim.constants import logger


def check_dependencies():
    def bin_is_present(binary):
        try:
            subprocess.Popen(
                binary,
                universal_newlines=True,
                shell=False,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
            )
        except OSError:
            return False
        else:
            return True

    all_bins = {
        "gifsicle": "GIF compression tool, part of `gifsicle` package",
        "pngquant": "PNG compression tool, part of `pngquant` package",
        "advdef": "PNG compression tool, part of `advancecomp` package",
        "jpegoptim": "JPEG compression tool, part of `jpegoptim` package",
        "tar": "TAR archive extractor",
    }

    all_good = True
    has_zimwriter = True
    for binary, msg in all_bins.items():
        if not bin_is_present(binary):
            logger.error(f"\t*{binary}* binary missing. {msg}")
            all_good = False

    return all_good, has_zimwriter
