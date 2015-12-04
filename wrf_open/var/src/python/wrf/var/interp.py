from math import floor, ceil

import numpy as n
import numpy.ma as ma

from wrf.var.extension import interpz3d,interpz2d,interp1d

__all__ = ["get_interplevel", "get_vertcross"]

def get_interplevel(data3d,zdata,desiredloc,missingval=-99999):
    """Return the horizontally interpolated data at the provided level
    
    data3d - the 3D field to interpolate
    zdata - the vertical values (height or pressure)
    desiredloc - the vertical level to interpolate at (must be same units as
    zdata)
    missingval - the missing data value (which will be masked on return)
    
    """
    r1 = interpz3d(data3d, zdata, desiredloc, missingval)
    masked_r1 = ma.masked_values (r1, missingval)
    return masked_r1

def _get_xy(xdim, ydim, pivot_point=None, angle=None, 
           start_point=None, end_point=None):
    """Returns the x,y points for the horizontal cross section line.
    
    xdim - maximum x-dimension
    ydim - maximum y-dimension
    pivot_point - a pivot point of (x,y) (must be used with angle)
    angle - the angle through the pivot point in degrees
    start_point - a start_point tuple of (x,y)
    end_point - an end point tuple of (x,y)
    
    """ 
    
    # Have a pivot point with an angle to find cross section
    if pivot is not None and angle is not None:
        xp = pivot_point[0]
        yp = pivot_point[1]
        
        if (angle > 315.0 or angle < 45.0 
            or ((angle > 135.0) and (angle < 225.0))):
            
            #x = y*slope + intercept
            slope = -(360.-angle)/45.
            if( angle < 45. ):
                slope = angle/45.
            if( angle > 135.):
                slope = (angle-180.)/45.
            
            intercept = xp - yp*slope
            
            # find intersections with domain boundaries
            y0 = 0.
            x0 = y0*slope + intercept
            
            if( x0 < 0.):  # intersect outside of left boundary
                x0 = 0.
                y0 =  (x0 - intercept)/slope
            if( x0 > xdim-1):  #intersect outside of right boundary
                x0 = xdim-1
                y0 =  (x0 - intercept)/slope
            y1 = ydim-1.  #need to make sure this will be a float?
            x1 = y1*slope + intercept
            
            if( x1 < 0.):  # intersect outside of left boundary
                x1 = 0.
                y1 =  (x1 - intercept)/slope
            
            if( x1 > xdim-1):  # intersect outside of right boundary
                x1 = xdim-1
                y1 =  (x1 - intercept)/slope
        else:
            #  y = x*slope + intercept
            slope = (90.-angle)/45.
            if( angle > 225. ):
                slope = (270.-angle)/45.
            intercept = yp - xp*slope

            #find intersections with domain boundaries
            x0 = 0.
            y0 = x0*slope + intercept
            
            if( y0 < 0.):  # intersect outside of bottom boundary
                y0 = 0.
                x0 =  (y0 - intercept)/slope
            
            if( y0 > ydim-1):  # intersect outside of top boundary
                y0 = ydim-1
                x0 =  (y0 - intercept)/slope
            
            x1 = xdim-1.  #  need to make sure this will be a float?
            y1 = x1*slope + intercept
            
            if( y1 < 0.):  # intersect outside of bottom boundary
                y1 = 0.
                x1 =  (y1 - intercept)/slope
            
            if( y1 > ydim-1):# intersect outside of top boundary
                y1 = ydim1
                x1 =  (y1 - intercept)/slope
    elif start_point is not None and end_point is not None:
        x0 = start_point[0]
        y0 = start_point[1]
        x1 = end_point[0]
        y1 = end_point[1]
        if ( x1 > xdim-1 ): 
            x1 = xdim
        if ( y1 > ydim-1): 
            y1 = ydim
    else:
        raise ValueError("invalid combination of None arguments")
    
    dx = x1 - x0
    dy = y1 - y0
    distance = (dx*dx + dy*dy)**0.5
    npts = int(distance)
    dxy = distance/npts
    
    xz = n.zeros((npts,2), "float")

    dx = dx/npts
    dy = dy/npts
    
    for i in xrange(npts):
        xy[i,0] = x0 + i*dx
        xy[i,1] = y0 + i*dy
        
    return xy


# TODO:  Add flag to use lat/lon points by doing conversion
def get_vertcross(data3d, z, missingval=-99999, 
                  pivot=None,angle=None,start_point=None,end_point=None):
    
    xdim = z.shape[2]
    ydim = z.shape[1]
    
    xy = _get_xy(xdim, ydim, pivot_point, angle, start_point, end_point)
    
    # Interp z
    var2dz   = interpz2d(z, xy)
    
    #  interp to constant z grid
    if(var2dz[0,0] > var2dz[1,0]):  # monotonically decreasing coordinate
        z_max = floor(n.amax(z)/10)*10     # bottom value
        z_min = ceil(n.amin(z)/10)*10      # top value
        dz = 10
        nlevels = int( (z_max-z_min)/dz)
        z_var2d = n.zeros((nlevels), dtype=z.dtype)
        z_var2d[0] = z_max
        dz = -dz
    else:
        z_max = n.amax(z)
        z_min = 0.
        dz = 0.01 * z_max
        nlevels = int( z_max/dz )
        z_var2d = n.zeros((nlevels), dtype=z.dtype)
        z_var2d[0] = z_min
    
    for i in xrange(1,nlevels):
        z_var2d[i] = z_var2d[0] + i*dz
        
    #interp the variable
    
    var2d = n.zeros((nlevels, xy.shape[0]),dtype=var2dz.dtype)
    var2dtmp = interpz2d(data3d, xy)
    
    for i in xrange(xy.shape[0]):
        var2d[:,i] = interp1d(var2dtmp[:,i], var2dz[:,i], z_var2d, missingval)
        
    return ma.masked_values(var2d, missingval)
        
    
    
    
    