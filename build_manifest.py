import zipfile
import os

manifest_dir = "./appPackage"
output_file = "manifest.zip"

with zipfile.ZipFile(output_file, "w") as zipf:
    for filename in os.listdir(manifest_dir):
        filepath = os.path.join(manifest_dir, filename)
        zipf.write(filepath, filename)
        print(f"  Added: {filename}")

print(f"\n✅ {output_file} created successfully!")