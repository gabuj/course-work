from astropy.io import fits
import numpy as np
from scipy.ndimage import gaussian_filter

# Load the FITS file
file_path = "/Users/yuri/Desktop/Year 3 Lab/Astronomical Image Processing/Astro/Fits_Data/fakeimage - 4.fits"
with fits.open(file_path) as hdul:
    image_data = hdul[0].data.copy()  # Copy of the 2D array of pixel values

# Parameters
background_threshold = 1  # Consider anything less than 1 as background
max_radius = 100  # Limit search radius for a more realistic boundary
output_image = image_data.copy()  # Image for marking centers and circles
galaxy_count = 0  # Counter for detected galaxies

# Loop to detect galaxies until no significant peak remains
while True:
    # Step 1: Find the highest pixel in the image (galaxy center)
    highest_pixel_value = image_data.max()
    if highest_pixel_value < 10:  # Stop if no significant peaks remain
        break

    # Find the coordinates of the highest pixel in the image
    highest_pixel_coords = np.unravel_index(np.argmax(image_data), image_data.shape)
    center_y, center_x = highest_pixel_coords
    galaxy_count += 1
    print(f"Galaxy {galaxy_count} detected at Center: ({center_x}, {center_y}), Peak Brightness: {highest_pixel_value}")

    # Step 2: Calculate radial distances from the highest pixel (assumed center)
    y_indices, x_indices = np.indices(image_data.shape)
    radii = np.sqrt((x_indices - center_x) ** 2 + (y_indices - center_y) ** 2)
    radii = radii.astype(int)

    # Step 3: Calculate the radial intensity profile by averaging pixel values at each radius
    radial_profile = np.array([image_data[radii == r].mean() for r in range(max_radius)])

    # Step 4: Smooth the radial profile to reduce noise
    smoothed_profile = gaussian_filter(radial_profile, sigma=2)

    # Step 5: Compute the gradient of the smoothed profile
    gradient = np.diff(smoothed_profile)

    # Step 6: Find the largest gradient drop that transitions to the background level (p2 just below 1)
    valid_drops = []
    peak_brightness = smoothed_profile[0]  # Initial peak for reference

    # Primary Condition: Look for p2 values in the range [0.8, 1)
    for j in range(1, len(gradient) - 1):  # Skip boundary values
        # Calculate p1 and p2 for the gradient at this point
        p1 = smoothed_profile[j]
        p2 = smoothed_profile[j + 1]

        # Priority 1: p2 must be between 0.8 and 1
        if 0.8 <= p2 < 1:
            # Calculate the gradient: (p1 - p2) / (r1 - r2)
            gradient_value = gradient[j]
            valid_drops.append((j, gradient_value))  # Append (index, gradient) tuples

    # Check if any valid drops were found in the primary condition
    if valid_drops:
        # Sort by proximity to the center (ascending) since the gradient values should all meet Priority 1
        valid_drops = sorted(valid_drops, key=lambda x: x[0])
        threshold_radius = valid_drops[0][0]  # Get the radius corresponding to the closest valid drop
    else:
        # Fallback Condition for Blended Galaxies: Look for the minimum gradient in the entire range
        min_gradient_index = np.argmin(gradient)
        p2_at_min_gradient = smoothed_profile[min_gradient_index + 1]  # p2 at the minimum gradient

        # Check if the p2 value at this minimum gradient is within a reasonable radius (to avoid boundary noise)
        if min_gradient_index < max_radius:
            threshold_radius = min_gradient_index
            print("Fallback condition applied: Using minimum gradient as boundary for blended galaxy.")
        else:
            # Raise an error if no valid drop points were found even after fallback
            raise ValueError("No valid drop points found - check the image or algorithm settings.")

    # Step 7: Draw the circle at the detected boundary radius
    circle_mask = (radii >= threshold_radius - 1) & (radii <= threshold_radius + 1)
    output_image[circle_mask] = output_image.max()  # Set circle to max value for visibility

    # Mark the highest pixel (center) in black
    min_value = image_data.min()
    output_image[center_y, center_x] = min_value  # Mark the center in black

    # Mask out the detected galaxy to continue searching for others
    image_data[radii <= threshold_radius] = min_value  # Mask detected galaxy

    print(f"Galaxy {galaxy_count} - Radius: {threshold_radius}, Center: ({center_x}, {center_y})")

# Step 8: Save the modified data to a new FITS file with circles and centers marked
output_path = "/Users/yuri/Desktop/Year 3 Lab/Astronomical Image Processing/Astro/Fits_Data/fakeimage_results.fits"
hdu = fits.PrimaryHDU(output_image)
hdul_with_circles = fits.HDUList([hdu])
hdul_with_circles.writeto(output_path, overwrite=True)

print(f"Final output saved to {output_path}")