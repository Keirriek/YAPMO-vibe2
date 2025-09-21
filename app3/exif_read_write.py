'''
Velden die een datum bevatten:
Composite:DateTimeCreated: 2005:03:05 14:33:13
IPTC:DateCreated: 2005:03:05
IPTC:TimeCreated: 14:33:13
XMP:ModifyDate: 2005:03:05 14:33:13
XMP:DateCreated: 2005:03:05 14:33:13
XMP:CreateDate: 2005:03:05 14:33:13
EXIF:DateTimeOriginal: 2005:03:05 14:33:13
EXIF:CreateDate: 2005:03:05 14:33:13
IPTC:Keywords: ['Ernst-Jan', 'Saskia', 'Ook hier', 'Vakantie', 'Wintersport']
XMP:Subject: ['Ernst-Jan', 'Saskia', 'Vakantie', 'Wintersport']
XMP:HierarchicalSubject: ['Ernst-Jan', 'Saskia', 'mijn toevoeging|2e toevoeging', 'Vakantie|Wintersport']
File:FileName: DSC00018.JPG
File:Directory: /workspace/Pictures-test/Small-test


'''


import subprocess
import json
import time
metadata_from_image = []
def get_exif_data_json(image_path):
    """Haal metadata op in JSON formaat voor de structuur"""
    try:
        result = subprocess.run(
            ['exiftool', '-j', '-G', '-a', '-u', '-charset', 'filename=utf8', image_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'  # Gebruik 'replace' voor ongeldige karakters
        )
        metadata = json.loads(result.stdout)[0]
        return metadata
    except Exception as e:
        # print(f"Error reading metadata (JSON): {e}")
        ui.notify(f"Error reading metadata (JSON): {e}",type='warning')
        return None

def get_exif_data_no_json(image_path):
    """Haal metadata op in plain text formaat voor de weergave"""
    try:
        result = subprocess.run(
            ['exiftool', '-G', '-a', '-u', '-charset', 'filename=utf8', image_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'  # Gebruik 'replace' voor ongeldige karakters
        )
        
        metadata = {}
        for line in result.stdout.splitlines():
            if ': ' in line:
                key, value = line.split(': ', 1)
                metadata[key.strip()] = value.strip()
        return metadata
    except Exception as e:
        # print(f"Error reading metadata (no JSON): {e}")
        ui.notify(f"Error reading metadata (no JSON): {e}",type='warning')
        return None

def get_exif_data(image_path):
    """Compatibiliteitsfunctie die de JSON versie gebruikt"""
    return get_exif_data_json(image_path)

def show_metadata_in_label(choses_picture):
    metadata = get_exif_data(choses_picture)
    
    if metadata:
        # Create a nicely formatted string with metadata
        metadata_text = ""
        # Clear previous metadata
        # metadata_from_image.clear()  # Uncommented to clear previous entries
        # metadata_from_image.append('Dit is de metadata:')
        for key, value in metadata.items():
            metadata_text += f"{key}: {value}\n"  # Format each key-value pair
            pass  # Doe niets, alleen metadata ophalen
    else:
        # metadata_from_image.append('No metadata available')
        # print('No metadata available')  # Deze kunnen we laten staan als error melding
        messagebox.showerror('Error', 'No metadata available')

def put_exif_data(image_path, metadata):
    try:
        # Maak een tijdelijk JSON-bestand met de metadata
        with open('temp_metadata.json', 'w') as f:
            json.dump([metadata], f)  # exiftool verwacht een lijst met één object
        
        # Gebruik exiftool om de metadata te schrijven
        # -overwrite_original voorkomt dat er backup bestanden worden gemaakt
        result = subprocess.run(
            ['exiftool', '-json=temp_metadata.json', '-overwrite_original', image_path],
            capture_output=True,
            text=True
        )
        
        # Verwijder het tijdelijke bestand
        subprocess.run(['rm', 'temp_metadata.json'])
        
        if result.returncode != 0:
            raise Exception(f"Exiftool error: {result.stderr}")
            
        return True
        
    except Exception as e:
        # print(f"Error writing metadata: {e}")
        ui.notify(f"Error writing metadata: {e}",type='negative')
        return False

def put_exif_data2(image_path, metadata):
    try:
        # Bouw de exiftool commando's op voor elke metadata waarde
        commands = []
        for key, value in metadata.items():
            if value is not None:  # Skip None values
                # Strip de groep prefix (bijv. 'XMP:' of 'EXIF:') als die er is
                tag = key.split(':')[-1] if ':' in key else key
                # Voeg de command toe
                commands.append(f'-{tag}={value}')
        if not commands:
            return False  # Geen geldige metadata om te schrijven
        # Voer exiftool uit met alle commands
        result = subprocess.run(
            ['exiftool', '-overwrite_original'] + commands + [image_path],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise Exception(f"Exiftool error: {result.stderr}")
        return True
    except Exception as e:
        # print(f"Error writing metadata: {e}")
        ui.notify(f"Error writing metadata: {e}",type='negative')
        return False

# def test_performance(image_path, metadata, iterations=100):
#     # Test put_exif_data (met JSON)
#     start_time = time.time()
#     for _ in range(iterations):
#         put_exif_data(image_path, metadata)
#     json_time = time.time() - start_time
    
#     # Test put_exif_data2 (direct commands)
#     start_time = time.time()
#     for _ in range(iterations):
#         put_exif_data2(image_path, metadata)
#     direct_time = time.time() - start_time
    
#     print(f"Performance test results ({iterations} iterations):")
#     print(f"put_exif_data (JSON method): {json_time:.2f} seconds")
#     print(f"put_exif_data2 (direct method): {direct_time:.2f} seconds")
#     print(f"Difference: put_exif_data2 is {(json_time/direct_time):.2f}x faster")

if __name__ == '__main__':
    path='/workspace/Pictures-test/Small-test/DSC00018.JPG'
    # Voorbeeld gebruik:
    metadata = {
        # 'Subject': 'Test onderwerp 2e keer',
        # 'Description': 'Test beschrijving 2e keer',
        # 'XMP:HierarchicalSubject': ['Ernst-Jan', 'Saskia','mijn toevoeging|3e toevoeging', 'Vakantie|Wintersport'],
        'IPTC:Keywords': ['Ernst-Jan', 'Saskia','Ook hier 3e keer', 'Vakantie', 'Wintersport']
    }
    put_exif_data2(path, metadata)

    # f=get_exif_data('/workspace/Pictures-test/Small-test/DSC00293.JPG')
    # # print(f)
    show_metadata_in_label(path)
    # print("metadata_from_image", metadata_from_image)

    # Test voorbeeld:
    # test_metadata = {
    #     'Subject': 'Test',
    #     'Description': 'Performance test'
    # }
    # test_performance('/pad/naar/foto.jpg', test_metadata)