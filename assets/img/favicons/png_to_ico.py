
import argparse
from PIL import Image

def png_to_ico(input_file, output_file, sizes):
    """
    Converts a PNG file to an ICO file.

    Args:
        input_file (str): The path to the input PNG file.
        output_file (str): The path to the output ICO file.
        sizes (list): A list of tuples representing the desired icon sizes.
    """
    try:
        img = Image.open(input_file)
        img.save(output_file, format="ICO", sizes=sizes)
        print(f"Successfully converted {input_file} to {output_file}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a PNG file to an ICO file.")
    parser.add_argument("input_file", help="The path to the input PNG file.")
    parser.add_argument("output_file", help="The path to the output ICO file.")
    parser.add_argument(
        "--sizes",
        nargs="+",
        type=int,
        default=[16, 32, 48, 64, 128, 256],
        help="A list of desired icon sizes (e.g., --sizes 16 32 48).",
    )
    args = parser.parse_args()

    # Convert the flat list of sizes to a list of tuples
    icon_sizes = [(size, size) for size in args.sizes]

    png_to_ico(args.input_file, args.output_file, icon_sizes)
