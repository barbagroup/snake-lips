"""Create the modified cross-sections of the gliding snake."""

from matplotlib import pyplot
import numpy
import os
import pathlib
import urllib.request


def reshape_lip(x, y, reverse=False):
    """Reshape the lip."""
    s = -1 if reverse else 1
    x, y = s * x[::s], y[::s]
    # Define the line along the first segment.
    a = (y[1] - y[0]) / (x[1] - x[0])
    b = y[0] - a * x[0]
    # Define the intersection between the line and
    # the horizontal line passing through the last point.
    yi = y[-1]
    xi = (yi - b) / a
    # Compute the distance between the first point and the intersection.
    dist = numpy.sqrt((x[0] - xi)**2 + (y[0] - yi)**2)
    # Define the point at distance `dist` from the intersection
    # along the horizontal line.
    x_im, y_im = xi + dist, yi
    # Define the line that bisects the first line and the horizontal line.
    x_mid, y_mid = (x[0] + x_im) / 2, (y[0] + y_im) / 2
    a = (y_mid - yi) / (x_mid - xi)
    b = yi - a * xi
    # Define the incircle contained between the first line and
    # the horizontal line that passes through the first point.
    xc, yc = x_im, a * x_im + b
    R = numpy.sqrt((xc - x_im)**2 + (yc - y_im)**2)
    theta = numpy.linspace(0.0, 2 * numpy.pi, num=50)[:-1]
    x_circ, y_circ = xc + R * numpy.cos(theta), yc + R * numpy.sin(theta)
    # Keep the arc between the first point and the image point.
    mask = numpy.where((x_circ < xc) & (y_circ < y[0]))[0]
    x_arc, y_arc = x_circ[mask], y_circ[mask]
    # Create the horizontal line between the image point and the last point.
    x_h = numpy.linspace(x_im, x[-1], num=10)
    y_h = y[-1] * numpy.ones_like(x_h)
    # Define the geometry of the new lip.
    x_lip = numpy.append(numpy.insert(x_arc, 0, x[0]), x_h)
    y_lip = numpy.append(numpy.insert(y_arc, 0, y[0]), y_h)
    return s * x_lip[::s], y_lip[::s]


def truncate_curve(x, y, length):
    """Truncate a curve to target a given length."""
    # Compute cumulative sum of the segments length.
    segment_lengths = numpy.sqrt((x[1:] - x[:-1])**2 + (y[1:] - y[:-1])**2)
    cumul = numpy.cumsum(numpy.insert(segment_lengths, 0, 0.0))
    # Find the index of the point just before reaching the distance.
    idx = numpy.where(cumul < length)[0][-1]
    # Interpolate the point between indices `idx` and `idx + 1`.
    extra_length = length - cumul[idx]  # remainder
    segment_length = cumul[idx + 1] - cumul[idx]
    alpha = extra_length / segment_length
    xi = x[idx] + alpha * (x[idx + 1] - x[idx])
    yi = y[idx] + alpha * (y[idx + 1] - y[idx])
    # Keep the section of interest.
    xs = numpy.append(x[:idx + 1], xi)
    ys = numpy.append(y[:idx + 1], yi)
    return xs, ys


def extract_lip(x, y, tip, lengths):
    """Extract a lip from the snake cross-section."""
    # Get the left part of the lip.
    xl, yl = truncate_curve(x[tip::-1], y[tip::-1], lengths[0])
    # Get the right part of the lip.
    xr, yr = truncate_curve(x[tip:], y[tip:], lengths[1])
    # Concatenate the left and right parts of the lip.
    x_lip = numpy.concatenate((xl[::-1], xr[1:]))
    y_lip = numpy.concatenate((yl[::-1], yr[1:]))
    return x_lip, y_lip


# Define the root directory.
rootdir = pathlib.Path(__file__).absolute().parents[1]
datadir = rootdir / 'data'
datadir.mkdir(parents=True, exist_ok=True)
figdir = rootdir / 'figures'
figdir.mkdir(parents=True, exist_ok=True)

# Retrieve the dataset of the cross-section from figshare.
filepath = datadir / 'snake_figshare.txt'
url = 'https://ndownloader.figshare.com/files/3088811'
urllib.request.urlretrieve(url, filepath)

# Load the coordinates from file.
with open(filepath, 'r') as infile:
    xo, yo = numpy.loadtxt(infile, dtype=numpy.float64, unpack=True)

# Scale the cross-section to have a chord-length of 1.
chord = xo.max() - xo.min()
x = xo / chord
y = yo / chord
chord = x.max() - x.min()
assert chord == 1.0

# Center the geometry at point (0, 0).
x -= (x.max() + x.min()) / 2
y -= (y.max() + y.min()) / 2
# Save the coordinates to file.
filepath = datadir / 'snake_both.txt'
with open(filepath, 'w') as outfile:
    numpy.savetxt(outfile, numpy.c_[x, y], header='{} points'.format(x.size))

models = {'both': [x, y]}

# Find the index of the tip on the front lip.
# The tip is defined as the point on the left side (negative x-coordinate)
# with the smallest y-coordinate.
tip = numpy.where((x < 0.0) & (y == y[x < 0.0].min()))[0][0]
# Get the front lip.
# The lip starts at 15% of the chord length from the tip on the upper surface.
# The lip ends at 25% of the chord length from the tip on the lower surface.
lengths = [0.15 * chord, 0.25 * chord]
x_front, y_front = extract_lip(x, y, tip, lengths)
# Reshape the lip.
x_front_mod, y_front_mod = reshape_lip(x_front, y_front)

# Define the cross-section missing the front lip.
idx1 = numpy.sqrt((x - x_front[0])**2 + (y - y_front[0])**2).argmin()
idx2 = numpy.sqrt((x - x_front[-1])**2 + (y - y_front[-1])**2).argmin()
x_nofront = numpy.concatenate((x[:idx1], x_front_mod, x[idx2 + 1:]))
y_nofront = numpy.concatenate((y[:idx1], y_front_mod, y[idx2 + 1:]))
# Save coordinates to file.
filepath = datadir / 'snake_nofront.txt'
with open(filepath, 'w') as outfile:
    numpy.savetxt(outfile, numpy.c_[x_nofront, y_nofront],
                  header='{} points'.format(x_nofront.size))

# Find the index of the tip on the back lip.
# The tip is defined as the point on the right side (negative x-coordinate)
# with the smallest y-coordinate.
tip = numpy.where((x > 0.0) & (y == y[x > 0.0].min()))[0][0]
# Get the back lip.
# The lip starts at 15% of the chord length from the tip on the upper surface.
# The lip ends at 25% of the chord length from the tip on the lower surface.
lengths = [0.25 * chord, 0.15 * chord]
x_back, y_back = extract_lip(x, y, tip, lengths)
# Reshape the lip.
x_back_mod, y_back_mod = reshape_lip(x_back, y_back, reverse=True)

# Define the cross-section missing the back lip.
idx3 = numpy.sqrt((x - x_back[0])**2 + (y - y_back[0])**2).argmin()
idx4 = numpy.sqrt((x - x_back[-1])**2 + (y - y_back[-1])**2).argmin()
x_noback = numpy.concatenate((x[:idx3], x_back_mod, x[idx4 + 1:]))
y_noback = numpy.concatenate((y[:idx3], y_back_mod, y[idx4 + 1:]))
# Save coordinates to file.
filepath = datadir / 'snake_noback.txt'
with open(filepath, 'w') as outfile:
    numpy.savetxt(outfile, numpy.c_[x_noback, y_noback],
                  header='{} points'.format(x_noback.size))

# Define the cross-section missing both lips.
x_nolips = numpy.concatenate((x[:idx1], x_front_mod, x[idx2 + 1:idx3],
                              x_back_mod, x[idx4 + 1:]))
y_nolips = numpy.concatenate((y[:idx1], y_front_mod, y[idx2 + 1:idx3],
                              y_back_mod, y[idx4 + 1:]))
# Save coordinates to file.
filepath = datadir / 'snake_nolips.txt'
with open(filepath, 'w') as outfile:
    numpy.savetxt(outfile, numpy.c_[x_nolips, y_nolips],
                  header='{} points'.format(x_nolips.size))

# Plot the geometries.
pyplot.rc('font', family='serif', size=16)
fig, ax = pyplot.subplots(ncols=4, figsize=(12.0, 4.0))
for i, axi in enumerate(ax):
    if i == 0:
        axi.plot(x, y, color='black', linewidth=3)
    else:
        axi.plot(x, y, color='black', linestyle=':')
    axi.axis('off')
    axi.axis('scaled', adjustable='box')
    axi.set_xlim(-0.52, 0.52)
    axi.set_ylim(-0.25, 0.25)
ax[1].plot(x_nofront, y_nofront, color='black', linewidth=3)
ax[2].plot(x_noback, y_noback, color='black', linewidth=3)
ax[3].plot(x_nolips, y_nolips, color='black', linewidth=3)
fig.tight_layout()
# Save the figure.
filepath = figdir / 'snake_geometries.png'
fig.savefig(filepath)

pyplot.show()
