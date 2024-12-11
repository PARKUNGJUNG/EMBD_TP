
import os
from huskylib import HuskyLensLibrary
import sys

def capture_image_and_save(huskyLens, save_directory, file_name="default.jpg"):
    """
    Captures a screenshot from HuskyLens and saves it to the given directory with
    the specified file name.

    :param huskyLens: Instance of HuskyLensLibrary initialized with appropriate settings
    :param save_directory: Directory where image will be saved
    :param file_name: Name of the output file
    """
    # Ensure the save directory exists
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    # Command HuskyLens to save a screenshot to its SD Card
    response = huskyLens.savePictureToSDCard()
    if response:
        print("Screenshot captured and saved successfully on HuskyLens SD card.")

        # Fake example, if HuskyLens provided a direct save path to host computer.
        file_path = os.path.join(save_directory, file_name)
        print(f"Copy the captured image manually from HuskyLens to: {file_path}")


        # Ensure the naming path or alternative instructions on path handoff

if __name__ == "__main__":
    try:
        save_directory = input("Enter the directory where the image should be saved: ").strip()
        file_name = input("Enter the file name for the saved image (e.g., image.jpg): ").strip()
        huskyLens = HuskyLensLibrary("I2C")  # Example initialization command for HuskyLens, adjust as needed.
        capture_image_and_save(huskyLens, save_directory, file_name)
    except Exception as e:
        print(f"An error occurred: {e}")




