from collections import MutableSequence


class Line(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __repr__(self):
        return 'Line(start=%s, end=%s)' % (self.start, self.end)

    def __eq__(self, other):
        if not isinstance(other, Line):
            return NotImplemented
        return self.start == other.start and self.end == other.end

    def __ne__(self, other):
        if not isinstance(other, Line):
            return NotImplemented
        return not self == other

    def __getitem__(self, item):
        return self.bpoints()[item]

    def __len__(self):
        return 2

    # def joins_smoothly_with(self, previous, wrt_parameterization=False):
    #     """Checks if this segment joins smoothly with previous segment.  By
    #     default, this only checks that this segment starts moving (at t=0) in
    #     the same direction (and from the same positive) as previous stopped
    #     moving (at t=1).  To check if the tangent magnitudes also match, set
    #     wrt_parameterization=True."""
    #     if wrt_parameterization:
    #         return self.start == previous.end and np.isclose(
    #             self.derivative(0), previous.derivative(1))
    #     else:
    #         return self.start == previous.end and np.isclose(
    #             self.unit_tangent(0), previous.unit_tangent(1))

    def point(self, t):
        """returns the coordinates of the Bezier curve evaluated at t."""
        distance = self.end - self.start
        return self.start + distance*t

    # def length(self, t0=0, t1=1, error=None, min_depth=None):
    #     """returns the length of the line segment between t0 and t1."""
    #     return abs(self.end - self.start)*(t1-t0)

    # def ilength(self, s, s_tol=ILENGTH_S_TOL, maxits=ILENGTH_MAXITS,
    #             error=ILENGTH_ERROR, min_depth=ILENGTH_MIN_DEPTH):
    #     """Returns a float, t, such that self.length(0, t) is approximately s.
    #     See the inv_arclength() docstring for more details."""
    #     return inv_arclength(self, s, s_tol=s_tol, maxits=maxits, error=error,
    #                          min_depth=min_depth)

    def bpoints(self):
        """returns the Bezier control points of the segment."""
        return self.start, self.end

    def poly(self, return_coeffs=False):
        """returns the line as a Polynomial object."""
        p = self.bpoints()
        coeffs = ([p[1] - p[0], p[0]])
    #     if return_coeffs:
    #         return coeffs
    #     else:
    #         return np.poly1d(coeffs)
        return coeffs

    # def derivative(self, t=None, n=1):
    #     """returns the nth derivative of the segment at t."""
    #     assert self.end != self.start
    #     if n == 1:
    #         return self.end - self.start
    #     elif n > 1:
    #         return 0
    #     else:
    #         raise ValueError("n should be a positive integer.")

    # def unit_tangent(self, t=None):
    #     """returns the unit tangent of the segment at t."""
    #     assert self.end != self.start
    #     dseg = self.end - self.start
    #     return dseg/abs(dseg)

    # def normal(self, t=None):
    #     """returns the (right hand rule) unit normal vector to self at t."""
    #     return -1j*self.unit_tangent(t)

    # def curvature(self, t):
    #     """returns the curvature of the line, which is always zero."""
    #     return 0

    # # def icurvature(self, kappa):
    # #     """returns a list of t-values such that 0 <= t<= 1 and
    # #     seg.curvature(t) = kappa."""
    # #     if kappa:
    # #         raise ValueError("The .icurvature() method for Line elements will "
    # #                          "return an empty list if kappa is nonzero and "
    # #                          "will raise this exception when kappa is zero as "
    # #                          "this is true at every point on the line.")
    # #     return []

    # def reversed(self):
    #     """returns a copy of the Line object with its orientation reversed."""
    #     return Line(self.end, self.start)

    # def intersect(self, other_seg, tol=None):
    #     """Finds the intersections of two segments.
    #     returns a list of tuples (t1, t2) such that
    #     self.point(t1) == other_seg.point(t2).
    #     Note: This will fail if the two segments coincide for more than a
    #     finite collection of points.
    #     tol is not used."""
    #     if isinstance(other_seg, Line):
    #         assert other_seg.end != other_seg.start and self.end != self.start
    #         assert self != other_seg
    #         # Solve the system [p1-p0, q1-q0]*[t1, t2]^T = q0 - p0
    #         # where self == Line(p0, p1) and other_seg == Line(q0, q1)
    #         a = (self.start.real, self.end.real)
    #         b = (self.start.imag, self.end.imag)
    #         c = (other_seg.start.real, other_seg.end.real)
    #         d = (other_seg.start.imag, other_seg.end.imag)
    #         denom = ((a[1] - a[0])*(d[0] - d[1]) -
    #                  (b[1] - b[0])*(c[0] - c[1]))
    #         if np.isclose(denom, 0):
    #             return []
    #         t1 = (c[0]*(b[0] - d[1]) -
    #               c[1]*(b[0] - d[0]) -
    #               a[0]*(d[0] - d[1]))/denom
    #         t2 = -(a[1]*(b[0] - d[0]) -
    #                a[0]*(b[1] - d[0]) -
    #                c[0]*(b[0] - b[1]))/denom
    #         if 0 <= t1 <= 1 and 0 <= t2 <= 1:
    #             return [(t1, t2)]
    #         return []
    #     elif isinstance(other_seg, QuadraticBezier):
    #         t2t1s = bezier_by_line_intersections(other_seg, self)
    #         return [(t1, t2) for t2, t1 in t2t1s]
    #     elif isinstance(other_seg, CubicBezier):
    #         t2t1s = bezier_by_line_intersections(other_seg, self)
    #         return [(t1, t2) for t2, t1 in t2t1s]
    #     elif isinstance(other_seg, Arc):
    #         t2t1s = other_seg.intersect(self)
    #         return [(t1, t2) for t2, t1 in t2t1s]
    #     elif isinstance(other_seg, Path):
    #         raise TypeError(
    #             "other_seg must be a path segment, not a Path object, use "
    #             "Path.intersect().")
    #     else:
    #         raise TypeError("other_seg must be a path segment.")

    # def bbox(self):
    #     """returns the bounding box for the segment in the form
    #     (xmin, xmax, ymin, ymax)."""
    #     xmin = min(self.start.real, self.end.real)
    #     xmax = max(self.start.real, self.end.real)
    #     ymin = min(self.start.imag, self.end.imag)
    #     ymax = max(self.start.imag, self.end.imag)
    #     return xmin, xmax, ymin, ymax

    # def cropped(self, t0, t1):
    #     """returns a cropped copy of this segment which starts at
    #     self.point(t0) and ends at self.point(t1)."""
    #     return Line(self.point(t0), self.point(t1))

    # def split(self, t):
    #     """returns two segments, whose union is this segment and which join at
    #     self.point(t)."""
    #     pt = self.point(t)
    #     return Line(self.start, pt), Line(pt, self.end)

    # def radialrange(self, origin, return_all_global_extrema=False):
    #     """returns the tuples (d_min, t_min) and (d_max, t_max) which minimize
    #     and maximize, respectively, the distance d = |self.point(t)-origin|."""
    #     return bezier_radialrange(self, origin,
    #             return_all_global_extrema=return_all_global_extrema)

    # def rotated(self, degs, origin=None):
    #     """Returns a copy of self rotated by `degs` degrees (CCW) around the
    #     point `origin` (a complex number).  By default `origin` is either
    #     `self.point(0.5)`, or in the case that self is an Arc object,
    #     `origin` defaults to `self.center`."""
    #     return rotate(self, degs, origin=origin)

    # def translated(self, z0):
    #     """Returns a copy of self shifted by the complex quantity `z0` such
    #     that self.translated(z0).point(t) = self.point(t) + z0 for any t."""
    #     return translate(self, z0)

    # def scaled(self, sx, sy=None, origin=0j):
    #     """Scale transform.  See `scale` function for further explanation."""
    #     return scale(self, sx=sx, sy=sy, origin=origin)


class CubicBezier(object):
    # For compatibility with old pickle files.
    # _length_info = {'length': None, 'bpoints': None, 'error': None,
    #                 'min_depth': None}

    def __init__(self, start, control1, control2, end):
        self.start = start
        self.control1 = control1
        self.control2 = control2
        self.end = end

        # used to know if self._length needs to be updated
        # self._length_info = {'length': None, 'bpoints': None, 'error': None,
        #                      'min_depth': None}

    def __repr__(self):
        return 'CubicBezier(start=%s, control1=%s, control2=%s, end=%s)' % (
            self.start, self.control1, self.control2, self.end)

    def __eq__(self, other):
        if not isinstance(other, CubicBezier):
            return NotImplemented
        return self.start == other.start and self.end == other.end \
            and self.control1 == other.control1 \
            and self.control2 == other.control2

    def __ne__(self, other):
        if not isinstance(other, CubicBezier):
            return NotImplemented
        return not self == other

    def __getitem__(self, item):
        return self.bpoints()[item]

    def __len__(self):
        return 4

    # def is_smooth_from(self, previous, warning_on=True):
    #     """[Warning: The name of this method is somewhat misleading (yet kept
    #     for compatibility with scripts created using svg.path 2.0).  This
    #     method is meant only for d string creation and should not be used to
    #     check for kinks.  To check a segment for differentiability, use the
    #     joins_smoothly_with() method instead.]"""
    #     if warning_on:
    #         warn(_is_smooth_from_warning)
    #     if isinstance(previous, CubicBezier):
    #         return (self.start == previous.end and
    #                 (self.control1 - self.start) == (
    #                     previous.end - previous.control2))
    #     else:
    #         return self.control1 == self.start

    # def joins_smoothly_with(self, previous, wrt_parameterization=False):
    #     """Checks if this segment joins smoothly with previous segment.  By
    #     default, this only checks that this segment starts moving (at t=0) in
    #     the same direction (and from the same positive) as previous stopped
    #     moving (at t=1).  To check if the tangent magnitudes also match, set
    #     wrt_parameterization=True."""
    #     if wrt_parameterization:
    #         return self.start == previous.end and np.isclose(
    #             self.derivative(0), previous.derivative(1))
    #     else:
    #         return self.start == previous.end and np.isclose(
    #             self.unit_tangent(0), previous.unit_tangent(1))

    def point(self, t):
        """Evaluate the cubic Bezier curve at t using Horner's rule."""
        # algebraically equivalent to
        # P0*(1-t)**3 + 3*P1*t*(1-t)**2 + 3*P2*(1-t)*t**2 + P3*t**3
        # for (P0, P1, P2, P3) = self.bpoints()
        return self.start + t*(
            3*(self.control1 - self.start) + t*(
                3*(self.start + self.control2) - 6*self.control1 + t*(
                    -self.start + 3*(self.control1 - self.control2) + self.end
                )))

    # def length(self, t0=0, t1=1, error=LENGTH_ERROR, min_depth=LENGTH_MIN_DEPTH):
    #     """Calculate the length of the path up to a certain position"""
    #     if t0 == 0 and t1 == 1:
    #         if self._length_info['bpoints'] == self.bpoints() \
    #                 and self._length_info['error'] >= error \
    #                 and self._length_info['min_depth'] >= min_depth:
    #             return self._length_info['length']

    #     # using scipy.integrate.quad is quick
    #     if _quad_available:
    #         s = quad(lambda tau: abs(self.derivative(tau)), t0, t1,
    #                         epsabs=error, limit=1000)[0]
    #     else:
    #         s = segment_length(self, t0, t1, self.point(t0), self.point(t1),
    #                            error, min_depth, 0)

    #     if t0 == 0 and t1 == 1:
    #         self._length_info['length'] = s
    #         self._length_info['bpoints'] = self.bpoints()
    #         self._length_info['error'] = error
    #         self._length_info['min_depth'] = min_depth
    #         return self._length_info['length']
    #     else:
    #         return s

    # def ilength(self, s, s_tol=ILENGTH_S_TOL, maxits=ILENGTH_MAXITS,
    #             error=ILENGTH_ERROR, min_depth=ILENGTH_MIN_DEPTH):
    #     """Returns a float, t, such that self.length(0, t) is approximately s.
    #     See the inv_arclength() docstring for more details."""
    #     return inv_arclength(self, s, s_tol=s_tol, maxits=maxits, error=error,
    #                          min_depth=min_depth)

    def bpoints(self):
        """returns the Bezier control points of the segment."""
        return self.start, self.control1, self.control2, self.end

    def poly(self, return_coeffs=False):
        """Returns a the cubic as a Polynomial object."""
        p = self.bpoints()
        coeffs = (-p[0] + 3*(p[1] - p[2]) + p[3],
                  3*(p[0] - 2*p[1] + p[2]),
                  3*(-p[0] + p[1]),
                  p[0])
        # if return_coeffs:
        #     return coeffs
        # else:
        #     return np.poly1d(coeffs)
        return coeffs

    # def derivative(self, t, n=1):
    #     """returns the nth derivative of the segment at t.
    #     Note: Bezier curves can have points where their derivative vanishes.
    #     If you are interested in the tangent direction, use the unit_tangent()
    #     method instead."""
    #     p = self.bpoints()
    #     if n == 1:
    #         return 3*(p[1] - p[0])*(1 - t)**2 + 6*(p[2] - p[1])*(1 - t)*t + 3*(
    #             p[3] - p[2])*t**2
    #     elif n == 2:
    #         return 6*(
    #             (1 - t)*(p[2] - 2*p[1] + p[0]) + t*(p[3] - 2*p[2] + p[1]))
    #     elif n == 3:
    #         return 6*(p[3] - 3*(p[2] - p[1]) - p[0])
    #     elif n > 3:
    #         return 0
    #     else:
    #         raise ValueError("n should be a positive integer.")

    # def unit_tangent(self, t):
    #     """returns the unit tangent vector of the segment at t (centered at
    #     the origin and expressed as a complex number).  If the tangent
    #     vector's magnitude is zero, this method will find the limit of
    #     self.derivative(tau)/abs(self.derivative(tau)) as tau approaches t."""
    #     return bezier_unit_tangent(self, t)

    # def normal(self, t):
    #     """returns the (right hand rule) unit normal vector to self at t."""
    #     return -1j * self.unit_tangent(t)

    # def curvature(self, t):
    #     """returns the curvature of the segment at t."""
    #     return segment_curvature(self, t)

    # # def icurvature(self, kappa):
    # #     """returns a list of t-values such that 0 <= t<= 1 and
    # #     seg.curvature(t) = kappa."""
    # #     z = self.poly()
    # #     x, y = real(z), imag(z)
    # #     dx, dy = x.deriv(), y.deriv()
    # #     ddx, ddy = dx.deriv(), dy.deriv()
    # #
    # #     p = kappa**2*(dx**2 + dy**2)**3 - (dx*ddy - ddx*dy)**2
    # #     return polyroots01(p)

    # def reversed(self):
    #     """returns a copy of the CubicBezier object with its orientation
    #     reversed."""
    #     new_cub = CubicBezier(self.end, self.control2, self.control1,
    #                           self.start)
    #     if self._length_info['length']:
    #         new_cub._length_info = self._length_info
    #         new_cub._length_info['bpoints'] = (
    #             self.end, self.control2, self.control1, self.start)
    #     return new_cub

    # def intersect(self, other_seg, tol=1e-12):
    #     """Finds the intersections of two segments.
    #     returns a list of tuples (t1, t2) such that
    #     self.point(t1) == other_seg.point(t2).
    #     Note: This will fail if the two segments coincide for more than a
    #     finite collection of points."""
    #     if isinstance(other_seg, Line):
    #         return bezier_by_line_intersections(self, other_seg)
    #     elif (isinstance(other_seg, QuadraticBezier) or
    #           isinstance(other_seg, CubicBezier)):
    #         assert self != other_seg
    #         longer_length = max(self.length(), other_seg.length())
    #         return bezier_intersections(self, other_seg,
    #                                     longer_length=longer_length,
    #                                     tol=tol, tol_deC=tol)
    #     elif isinstance(other_seg, Arc):
    #         t2t1s = other_seg.intersect(self)
    #         return [(t1, t2) for t2, t1 in t2t1s]
    #     elif isinstance(other_seg, Path):
    #         raise TypeError(
    #             "other_seg must be a path segment, not a Path object, use "
    #             "Path.intersect().")
    #     else:
    #         raise TypeError("other_seg must be a path segment.")

    # def bbox(self):
    #     """returns the bounding box for the segment in the form
    #     (xmin, xmax, ymin, ymax)."""
    #     return bezier_bounding_box(self)

    # def split(self, t):
    #     """returns two segments, whose union is this segment and which join at
    #     self.point(t)."""
    #     bpoints1, bpoints2 = split_bezier(self.bpoints(), t)
    #     return CubicBezier(*bpoints1), CubicBezier(*bpoints2)

    # def cropped(self, t0, t1):
    #     """returns a cropped copy of this segment which starts at
    #     self.point(t0) and ends at self.point(t1)."""
    #     return CubicBezier(*crop_bezier(self, t0, t1))

    # def radialrange(self, origin, return_all_global_extrema=False):
    #     """returns the tuples (d_min, t_min) and (d_max, t_max) which minimize
    #     and maximize, respectively, the distance d = |self.point(t)-origin|."""
    #     return bezier_radialrange(self, origin,
    #             return_all_global_extrema=return_all_global_extrema)

    # def rotated(self, degs, origin=None):
    #     """Returns a copy of self rotated by `degs` degrees (CCW) around the
    #     point `origin` (a complex number).  By default `origin` is either
    #     `self.point(0.5)`, or in the case that self is an Arc object,
    #     `origin` defaults to `self.center`."""
    #     return rotate(self, degs, origin=origin)

    # def translated(self, z0):
    #     """Returns a copy of self shifted by the complex quantity `z0` such
    #     that self.translated(z0).point(t) = self.point(t) + z0 for any t."""
    #     return translate(self, z0)

    # def scaled(self, sx, sy=None, origin=0j):
    #     """Scale transform.  See `scale` function for further explanation."""
    #     return scale(self, sx=sx, sy=sy, origin=origin)


class Path(MutableSequence):
    """A Path is a sequence of path segments"""

    # Put it here, so there is a default if unpickled.
    _closed = False
    _start = None
    _end = None

    def __init__(self, *segments, **kw):
        self._segments = list(segments)
        self._length = None
        self._lengths = None
        if 'closed' in kw:
            self.closed = kw['closed']  # DEPRECATED
        if self._segments:
            self._start = self._segments[0].start
            self._end = self._segments[-1].end
        else:
            self._start = None
            self._end = None

    def __getitem__(self, index):
        return self._segments[index]

    def __setitem__(self, index, value):
        self._segments[index] = value
        self._length = None
        self._start = self._segments[0].start
        self._end = self._segments[-1].end

    def __delitem__(self, index):
        del self._segments[index]
        self._length = None
        self._start = self._segments[0].start
        self._end = self._segments[-1].end

    def __iter__(self):
        return self._segments.__iter__()

    def __contains__(self, x):
        return self._segments.__contains__(x)

    def insert(self, index, value):
        self._segments.insert(index, value)
        self._length = None
        self._start = self._segments[0].start
        self._end = self._segments[-1].end

    def reversed(self):
        """returns a copy of the Path object with its orientation reversed."""
        newpath = [seg.reversed() for seg in self]
        newpath.reverse()
        return Path(*newpath)

    def __len__(self):
        return len(self._segments)

    def __repr__(self):
        return "Path({})".format(
            ",\n     ".join(repr(x) for x in self._segments))

    def __eq__(self, other):
        if not isinstance(other, Path):
            return NotImplemented
        if len(self) != len(other):
            return False
        for s, o in zip(self._segments, other._segments):
            if not s == o:
                return False
        return True

    def __ne__(self, other):
        if not isinstance(other, Path):
            return NotImplemented
        return not self == other

    # def _calc_lengths(self, error=LENGTH_ERROR, min_depth=LENGTH_MIN_DEPTH):
    #     if self._length is not None:
    #         return

    #     lengths = [each.length(error=error, min_depth=min_depth) for each in
    #                self._segments]
    #     self._length = sum(lengths)
    #     self._lengths = [each/self._length for each in lengths]

    # def point(self, pos):

    #     # Shortcuts
    #     if pos == 0.0:
    #         return self._segments[0].point(pos)
    #     if pos == 1.0:
    #         return self._segments[-1].point(pos)

    #     self._calc_lengths()
    #     # Find which segment the point we search for is located on:
    #     segment_start = 0
    #     for index, segment in enumerate(self._segments):
    #         segment_end = segment_start + self._lengths[index]
    #         if segment_end >= pos:
    #             # This is the segment! How far in on the segment is the point?
    #             segment_pos = (pos - segment_start)/(
    #                 segment_end - segment_start)
    #             return segment.point(segment_pos)
    #         segment_start = segment_end

    # def length(self, T0=0, T1=1, error=LENGTH_ERROR, min_depth=LENGTH_MIN_DEPTH):
    #     self._calc_lengths(error=error, min_depth=min_depth)
    #     if T0 == 0 and T1 == 1:
    #         return self._length
    #     else:
    #         if len(self) == 1:
    #             return self[0].length(t0=T0, t1=T1)
    #         idx0, t0 = self.T2t(T0)
    #         idx1, t1 = self.T2t(T1)
    #         if idx0 == idx1:
    #             return self[idx0].length(t0=t0, t1=t1)
    #         return (self[idx0].length(t0=t0) +
    #                 sum(self[idx].length() for idx in range(idx0 + 1, idx1)) +
    #                 self[idx1].length(t1=t1))

    # def ilength(self, s, s_tol=ILENGTH_S_TOL, maxits=ILENGTH_MAXITS,
    #             error=ILENGTH_ERROR, min_depth=ILENGTH_MIN_DEPTH):
    #     """Returns a float, t, such that self.length(0, t) is approximately s.
    #     See the inv_arclength() docstring for more details."""
    #     return inv_arclength(self, s, s_tol=s_tol, maxits=maxits, error=error,
    #                          min_depth=min_depth)

    # def iscontinuous(self):
    #     """Checks if a path is continuous with respect to its
    #     parameterization."""
    #     return all(self[i].end == self[i+1].start for i in range(len(self) - 1))

    # def continuous_subpaths(self):
    #     """Breaks self into its continuous components, returning a list of
    #     continuous subpaths.
    #     I.e.
    #     (all(subpath.iscontinuous() for subpath in self.continuous_subpaths())
    #      and self == concatpaths(self.continuous_subpaths()))
    #     )
    #     """
    #     subpaths = []
    #     subpath_start = 0
    #     for i in range(len(self) - 1):
    #         if self[i].end != self[(i+1) % len(self)].start:
    #             subpaths.append(Path(*self[subpath_start: i+1]))
    #             subpath_start = i+1
    #     subpaths.append(Path(*self[subpath_start: len(self)]))
    #     return subpaths

    # def isclosed(self):
    #     """This function determines if a connected path is closed."""
    #     assert len(self) != 0
    #     assert self.iscontinuous()
    #     return self.start == self.end

    # def isclosedac(self):
    #     assert len(self) != 0
    #     return self.start == self.end

    # def _is_closable(self):
    #     end = self[-1].end
    #     for segment in self:
    #         if segment.start == end:
    #             return True
    #     return False

    # @property
    # def closed(self, warning_on=CLOSED_WARNING_ON):
    #     """The closed attribute is deprecated, please use the isclosed()
    #     method instead.  See _closed_warning for more information."""
    #     mes = ("This attribute is deprecated, consider using isclosed() "
    #            "method instead.\n\nThis attribute is kept for compatibility "
    #            "with scripts created using svg.path (v2.0). You can prevent "
    #            "this warning in the future by setting "
    #            "CLOSED_WARNING_ON=False.")
    #     if warning_on:
    #         warn(mes)
    #     return self._closed and self._is_closable()

    # @closed.setter
    # def closed(self, value):
    #     value = bool(value)
    #     if value and not self._is_closable():
    #         raise ValueError("End does not coincide with a segment start.")
    #     self._closed = value

    # @property
    # def start(self):
    #     if not self._start:
    #         self._start = self._segments[0].start
    #     return self._start

    # @start.setter
    # def start(self, pt):
    #     self._start = pt
    #     self._segments[0].start = pt

    # @property
    # def end(self):
    #     if not self._end:
    #         self._end = self._segments[-1].end
    #     return self._end

    # @end.setter
    # def end(self, pt):
    #     self._end = pt
    #     self._segments[-1].end = pt

    def d(self, useSandT=False, use_closed_attrib=False):
        """Returns a path d-string for the path object.
        For an explanation of useSandT and use_closed_attrib, see the
        compatibility notes in the README."""

        if use_closed_attrib:
            self_closed = self.closed(warning_on=False)
            if self_closed:
                segments = self[:-1]
            else:
                segments = self[:]
        else:
            self_closed = False
            segments = self[:]

        current_pos = None
        parts = []
        previous_segment = None
        end = self[-1].end

        for segment in segments:
            seg_start = segment.start
            # If the start of this segment does not coincide with the end of
            # the last segment or if this segment is actually the close point
            # of a closed path, then we should start a new subpath here.
            if current_pos != seg_start or \
                    (self_closed and seg_start == end and use_closed_attrib):
                parts.append('M {},{}'.format(seg_start.real, seg_start.imag))

            if isinstance(segment, Line):
                args = segment.end.real, segment.end.imag
                parts.append('L {},{}'.format(*args))
            elif isinstance(segment, CubicBezier):
                if useSandT and segment.is_smooth_from(previous_segment,
                                                       warning_on=False):
                    args = (segment.control2.real, segment.control2.imag,
                            segment.end.real, segment.end.imag)
                    parts.append('S {},{} {},{}'.format(*args))
                else:
                    args = (segment.control1.real, segment.control1.imag,
                            segment.control2.real, segment.control2.imag,
                            segment.end.real, segment.end.imag)
                    parts.append('C {},{} {},{} {},{}'.format(*args))
            # elif isinstance(segment, QuadraticBezier):
            #     if useSandT and segment.is_smooth_from(previous_segment,
            #                                            warning_on=False):
            #         args = segment.end.real, segment.end.imag
            #         parts.append('T {},{}'.format(*args))
            #     else:
            #         args = (segment.control.real, segment.control.imag,
            #                 segment.end.real, segment.end.imag)
            #         parts.append('Q {},{} {},{}'.format(*args))

            # elif isinstance(segment, Arc):
            #     args = (segment.radius.real, segment.radius.imag,
            #             segment.rotation,int(segment.large_arc),
            #             int(segment.sweep),segment.end.real, segment.end.imag)
            #     parts.append('A {},{} {} {:d},{:d} {},{}'.format(*args))
            current_pos = segment.end
            previous_segment = segment

        if self_closed:
            parts.append('Z')

        return ' '.join(parts)

    # def joins_smoothly_with(self, previous, wrt_parameterization=False):
    #     """Checks if this Path object joins smoothly with previous
    #     path/segment.  By default, this only checks that this Path starts
    #     moving (at t=0) in the same direction (and from the same positive) as
    #     previous stopped moving (at t=1).  To check if the tangent magnitudes
    #     also match, set wrt_parameterization=True."""
    #     if wrt_parameterization:
    #         return self[0].start == previous.end and self.derivative(
    #             0) == previous.derivative(1)
    #     else:
    #         return self[0].start == previous.end and self.unit_tangent(
    #             0) == previous.unit_tangent(1)

    # def T2t(self, T):
    #     """returns the segment index, `seg_idx`, and segment parameter, `t`,
    #     corresponding to the path parameter `T`.  In other words, this is the
    #     inverse of the `Path.t2T()` method."""
    #     if T == 1:
    #         return len(self)-1, 1
    #     if T == 0:
    #         return 0, 0
    #     self._calc_lengths()
    #     # Find which segment self.point(T) falls on:
    #     T0 = 0  # the T-value the current segment starts on
    #     for seg_idx, seg_length in enumerate(self._lengths):
    #         T1 = T0 + seg_length  # the T-value the current segment ends on
    #         if T1 >= T:
    #             # This is the segment!
    #             t = (T - T0)/seg_length
    #             return seg_idx, t
    #         T0 = T1

    #     assert 0 <= T <= 1
    #     raise BugException

    # def t2T(self, seg, t):
    #     """returns the path parameter T which corresponds to the segment
    #     parameter t.  In other words, for any Path object, path, and any
    #     segment in path, seg,  T(t) = path.t2T(seg, t) is the unique
    #     reparameterization such that path.point(T(t)) == seg.point(t) for all
    #     0 <= t <= 1.
    #     Input Note: seg can be a segment in the Path object or its
    #     corresponding index."""
    #     self._calc_lengths()
    #     # Accept an index or a segment for seg
    #     if isinstance(seg, int):
    #         seg_idx = seg
    #     else:
    #         try:
    #             seg_idx = self.index(seg)
    #         except ValueError:
    #             assert is_path_segment(seg) or isinstance(seg, int)
    #             raise

    #     segment_start = sum(self._lengths[:seg_idx])
    #     segment_end = segment_start + self._lengths[seg_idx]
    #     T = (segment_end - segment_start)*t + segment_start
    #     return T

    # def derivative(self, T, n=1):
    #     """returns the tangent vector of the Path at T (centered at the origin
    #     and expressed as a complex number).
    #     Note: Bezier curves can have points where their derivative vanishes.
    #     If you are interested in the tangent direction, use unit_tangent()
    #     method instead."""
    #     seg_idx, t = self.T2t(T)
    #     seg = self._segments[seg_idx]
    #     return seg.derivative(t, n=n)/seg.length()**n

    # def unit_tangent(self, T):
    #     """returns the unit tangent vector of the Path at T (centered at the
    #     origin and expressed as a complex number).  If the tangent vector's
    #     magnitude is zero, this method will find the limit of
    #     self.derivative(tau)/abs(self.derivative(tau)) as tau approaches T."""
    #     seg_idx, t = self.T2t(T)
    #     return self._segments[seg_idx].unit_tangent(t)

    # def normal(self, t):
    #     """returns the (right hand rule) unit normal vector to self at t."""
    #     return -1j*self.unit_tangent(t)

    # def curvature(self, T):
    #     """returns the curvature of this Path object at T and outputs
    #     float('inf') if not differentiable at T."""
    #     seg_idx, t = self.T2t(T)
    #     seg = self[seg_idx]
    #     if np.isclose(t, 0) and (seg_idx != 0 or self.end==self.start):
    #         previous_seg_in_path = self._segments[
    #             (seg_idx - 1) % len(self._segments)]
    #         if not seg.joins_smoothly_with(previous_seg_in_path):
    #             return float('inf')
    #     elif np.isclose(t, 1) and (seg_idx != len(self) - 1 or self.end==self.start):
    #         next_seg_in_path = self._segments[
    #             (seg_idx + 1) % len(self._segments)]
    #         if not next_seg_in_path.joins_smoothly_with(seg):
    #             return float('inf')
    #     dz = self.derivative(T)
    #     ddz = self.derivative(T, n=2)
    #     dx, dy = dz.real, dz.imag
    #     ddx, ddy = ddz.real, ddz.imag
    #     return abs(dx*ddy - dy*ddx)/(dx*dx + dy*dy)**1.5

    # # def icurvature(self, kappa):
    # #     """returns a list of T-values such that 0 <= T <= 1 and
    # #     seg.curvature(t) = kappa.
    # #     Note: not implemented for paths containing Arc segments."""
    # #     assert is_bezier_path(self)
    # #     Ts = []
    # #     for i, seg in enumerate(self):
    # #         Ts += [self.t2T(i, t) for t in seg.icurvature(kappa)]
    # #     return Ts

    # def area(self):
    #     """returns the area enclosed by this Path object.
    #     Note: negative area results from CW (as opposed to CCW)
    #     parameterization of the Path object."""
    #     assert self.isclosed()
    #     area_enclosed = 0
    #     for seg in self:
    #         x = real(seg.poly())
    #         dy = imag(seg.poly()).deriv()
    #         integrand = x*dy
    #         integral = integrand.integ()
    #         area_enclosed += integral(1) - integral(0)
    #     return area_enclosed

    # def intersect(self, other_curve, justonemode=False, tol=1e-12):
    #     """returns list of pairs of pairs ((T1, seg1, t1), (T2, seg2, t2))
    #     giving the intersection points.
    #     If justonemode==True, then returns just the first
    #     intersection found.
    #     tol is used to check for redundant intersections (see comment above
    #     the code block where tol is used).
    #     Note:  If the two path objects coincide for more than a finite set of
    #     points, this code will fail."""
    #     path1 = self
    #     if isinstance(other_curve, Path):
    #         path2 = other_curve
    #     else:
    #         path2 = Path(other_curve)
    #     assert path1 != path2
    #     intersection_list = []
    #     for seg1 in path1:
    #         for seg2 in path2:
    #             if justonemode and intersection_list:
    #                 return intersection_list[0]
    #             for t1, t2 in seg1.intersect(seg2, tol=tol):
    #                 T1 = path1.t2T(seg1, t1)
    #                 T2 = path2.t2T(seg2, t2)
    #                 intersection_list.append(((T1, seg1, t1), (T2, seg2, t2)))
    #     if justonemode and intersection_list:
    #         return intersection_list[0]

    #     # Note: If the intersection takes place at a joint (point one seg ends
    #     # and next begins in path) then intersection_list may contain a
    #     # redundant intersection.  This code block checks for and removes said
    #     # redundancies.
    #     if intersection_list:
    #         pts = [seg1.point(_t1) for _T1, _seg1, _t1 in list(zip(*intersection_list))[0]]
    #         indices2remove = []
    #         for ind1 in range(len(pts)):
    #             for ind2 in range(ind1 + 1, len(pts)):
    #                 if abs(pts[ind1] - pts[ind2]) < tol:
    #                     # then there's a redundancy. Remove it.
    #                     indices2remove.append(ind2)
    #         intersection_list = [inter for ind, inter in
    #                              enumerate(intersection_list) if
    #                              ind not in indices2remove]
    #     return intersection_list

    # def bbox(self):
    #     """returns a bounding box for the input Path object in the form
    #     (xmin, xmax, ymin, ymax)."""
    #     bbs = [seg.bbox() for seg in self._segments]
    #     xmins, xmaxs, ymins, ymaxs = list(zip(*bbs))
    #     xmin = min(xmins)
    #     xmax = max(xmaxs)
    #     ymin = min(ymins)
    #     ymax = max(ymaxs)
    #     return xmin, xmax, ymin, ymax

    # def cropped(self, T0, T1):
    #     """returns a cropped copy of the path."""
    #     assert 0 <= T0 <= 1 and 0 <= T1<= 1
    #     assert T0 != T1
    #     assert not (T0 == 1 and T1 == 0)

    #     if T0 == 1 and 0 < T1 < 1 and self.isclosed():
    #         return self.cropped(0, T1)

    #     if T1 == 1:
    #         seg1 = self[-1]
    #         t_seg1 = 1
    #         i1 = len(self) - 1
    #     else:
    #         seg1_idx, t_seg1 = self.T2t(T1)
    #         seg1 = self[seg1_idx]
    #         if np.isclose(t_seg1, 0):
    #             i1 = (self.index(seg1) - 1) % len(self)
    #             seg1 = self[i1]
    #             t_seg1 = 1
    #         else:
    #             i1 = self.index(seg1)
    #     if T0 == 0:
    #         seg0 = self[0]
    #         t_seg0 = 0
    #         i0 = 0
    #     else:
    #         seg0_idx, t_seg0 = self.T2t(T0)
    #         seg0 = self[seg0_idx]
    #         if np.isclose(t_seg0, 1):
    #             i0 = (self.index(seg0) + 1) % len(self)
    #             seg0 = self[i0]
    #             t_seg0 = 0
    #         else:
    #             i0 = self.index(seg0)

    #     if T0 < T1 and i0 == i1:
    #         new_path = Path(seg0.cropped(t_seg0, t_seg1))
    #     else:
    #         new_path = Path(seg0.cropped(t_seg0, 1))

    #         # T1<T0 must cross discontinuity case
    #         if T1 < T0:
    #             if not self.isclosed():
    #                 raise ValueError("This path is not closed, thus T0 must "
    #                                  "be less than T1.")
    #             else:
    #                 for i in range(i0 + 1, len(self)):
    #                     new_path.append(self[i])
    #                 for i in range(0, i1):
    #                     new_path.append(self[i])

    #         # T0<T1 straight-forward case
    #         else:
    #             for i in range(i0 + 1, i1):
    #                 new_path.append(self[i])

    #         if t_seg1 != 0:
    #             new_path.append(seg1.cropped(0, t_seg1))
    #     return new_path

    # def radialrange(self, origin, return_all_global_extrema=False):
    #     """returns the tuples (d_min, t_min, idx_min), (d_max, t_max, idx_max)
    #     which minimize and maximize, respectively, the distance
    #     d = |self[idx].point(t)-origin|."""
    #     if return_all_global_extrema:
    #         raise NotImplementedError
    #     else:
    #         global_min = (np.inf, None, None)
    #         global_max = (0, None, None)
    #         for seg_idx, seg in enumerate(self):
    #             seg_global_min, seg_global_max = seg.radialrange(origin)
    #             if seg_global_min[0] < global_min[0]:
    #                 global_min = seg_global_min + (seg_idx,)
    #             if seg_global_max[0] > global_max[0]:
    #                 global_max = seg_global_max + (seg_idx,)
    #         return global_min, global_max

    # def rotated(self, degs, origin=None):
    #     """Returns a copy of self rotated by `degs` degrees (CCW) around the
    #     point `origin` (a complex number).  By default `origin` is either
    #     `self.point(0.5)`, or in the case that self is an Arc object,
    #     `origin` defaults to `self.center`."""
    #     return rotate(self, degs, origin=origin)

    # def translated(self, z0):
    #     """Returns a copy of self shifted by the complex quantity `z0` such
    #     that self.translated(z0).point(t) = self.point(t) + z0 for any t."""
    #     return translate(self, z0)

    # def scaled(self, sx, sy=None, origin=0j):
    #     """Scale transform.  See `scale` function for further explanation."""
    #     return scale(self, sx=sx, sy=sy, origin=origin)
