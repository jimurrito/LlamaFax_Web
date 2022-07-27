from time import time
import logging


class prefTest:
    """Gets Preformance Metrics Test for Llamafax"""

    def __init__(self) -> None:
        self.docCount = 0
        self.startTime = time()

    def includeOne(self):
        """Adds to the doc count"""
        self.docCount += 1

    def stop(self, Include) -> float:
        """Stops Test, returns Documents per Second
        \nOptional: Include == files to include before stop"""
        self.docCount += Include
        return self.docCount / round((time() - self.startTime), ndigits=2)

    def vstop(self, Units="Messages") -> float:
        """Same as .stop(), but is verbose to console. Only works if logging is info or debug
        \nStops Test, returns Documents per Second
        """
        if self.docCount:
            logging.info(
                f"{round((self.docCount / round((time() - self.startTime),ndigits=2)),ndigits=2)} {Units} per Second Processed."
            )
            return
        logging.info("0 Messages Processed.")


def makeXDigits(Input: int, Mod: int = 10) -> str:
    """Sets Input strings with leading '0's to make the number a set amount of digits. (Mod)"""
    Digits = len([char for char in str(abs(Input))])
    if Digits >= Mod:
        return str(Input)
    return ("0" * (Mod - Digits)) + str(Input)


def main():
    pass


if __name__ == "__main__":
    main()
