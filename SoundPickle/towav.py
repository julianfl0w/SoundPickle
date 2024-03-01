import json
import base64
import sys

def load_json(filename):
    """Loads JSON data from a local file."""
    with open(filename, 'r') as file:
        return json.load(file)

def decode_and_save_mp3(data, filename):
    """Decodes base64 MP3 data and saves it to a file."""
    mp3_data = base64.b64decode(data)
    with open(filename, 'wb') as file:
        file.write(mp3_data)

def main(json_filename):
    output_filename = 'first_region.mp3'

    try:
        json_data = load_json(json_filename)
        first_region_mp3_data = json_data['regions'][0]['mp3Data']
        decode_and_save_mp3(first_region_mp3_data, output_filename)
        print(f'MP3 data successfully saved to {output_filename}')
    except Exception as e:
        print(f'An error occurred: {e}')

if __name__ == '__main__':
    main(sys.argv[1])
