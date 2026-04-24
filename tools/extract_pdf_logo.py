import argparse
import fitz  # PyMuPDF
import os
import sys
import urllib.request
import tempfile

def extract_largest_image_from_pdf(pdf_url, output_path):
    print(f"[*] Downloading PDF from {pdf_url}...")
    try:
        fd, temp_pdf = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        
        req = urllib.request.Request(pdf_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(temp_pdf, 'wb') as out_file:
            out_file.write(response.read())
            
        print("[*] Extracting images using PyMuPDF...")
        doc = fitz.open(temp_pdf)
        if len(doc) == 0:
            print("❌ Empty PDF")
            return False
            
        page = doc[0] # Usually logo is on the first page
        image_list = page.get_images(full=True)
        
        if not image_list:
            print("❌ No images found on the first page.")
            return False
            
        largest_image = None
        max_size = 0
        
        for img in image_list:
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]
            size = len(image_bytes)
            
            # Prefer PNG or JPEG, ignore tiny icons, also we know logos are somewhat large but not full page
            # Usually corporate logos on cover pages are the largest embedded image if it's a text-heavy cover.
            if size > max_size and ext in ['png', 'jpeg', 'jpg']:
                max_size = size
                largest_image = image_bytes
                
        if largest_image:
            with open(output_path, "wb") as f:
                f.write(largest_image)
            print(f"[OK] Logo saved to {output_path}")
            return True
        else:
            print("❌ Could not find a suitable logo image.")
            return False
            
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        return False
    finally:
        try: os.remove(temp_pdf)
        except: pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    success = extract_largest_image_from_pdf(args.url, args.output)
    sys.exit(0 if success else 1)
