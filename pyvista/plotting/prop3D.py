"""Prop3D module."""
import pyvista as pv


class Prop3D(pv._vtk.vtkProp3D):
    """Prop3D wrapper for VTK."""

    def __init__(self, mapper=None, prop=None):
        """Initialize Prop3D."""
        super().__init__()

    @property
    def scale(self) -> tuple:
        """Return or set actor scale.

        Examples
        --------
        Create an actor using the :class:`pyvista.Plotter` and then change the
        scale of the actor.

        >>> import pyvista as pv
        >>> pl = pv.Plotter()
        >>> actor = pl.add_mesh(pv.Sphere())
        >>> actor.scale = (2.0, 2.0, 2.0)
        >>> actor.scale
        (2.0, 2.0, 2.0)

        """
        return self.GetScale()

    @scale.setter
    def scale(self, value: tuple):
        return self.SetScale(value)

    @property
    def position(self):
        """Return or set the actor position.

        Examples
        --------
        Change the position of an actor. Note how this does not change the
        position of the underlying dataset, just the relative location of the
        actor in the :class:`pyvista.Plotter`.

        >>> import pyvista as pv
        >>> mesh = pv.Sphere()
        >>> pl = pv.Plotter()
        >>> _ = pl.add_mesh(mesh, color='b')
        >>> actor = pl.add_mesh(mesh, color='r')
        >>> actor.position = (0, 0, 1)  # shifts the red sphere up
        >>> pl.show()

        """
        return self.GetPosition()

    @position.setter
    def position(self, value: tuple):
        self.SetPosition(value)

    def rotate_x(self, angle: float):
        """Rotate the actor about the x axis.

        Parameters
        ----------
        angle : float
            Angle to rotate the actor about the x axis in degrees.

        Examples
        --------
        Rotate the actor about the x axis 45 degrees. Note how this does not
        change the location of the underlying dataset.

        >>> import pyvista as pv
        >>> mesh = pv.Cube()
        >>> pl = pv.Plotter()
        >>> _ = pl.add_mesh(mesh, color='b')
        >>> actor = pl.add_mesh(
        ...     mesh, color='r', style='wireframe', line_width=5, lighting=False,
        ... )
        >>> actor.rotate_x(45)
        >>> pl.show_axes()
        >>> pl.show()

        """
        self.RotateX(angle)

    def rotate_y(self, angle: float):
        """Rotate the actor about the y axis.

        Parameters
        ----------
        angle : float
            Angle to rotate the actor about the y axis in degrees.

        Examples
        --------
        Rotate the actor about the y axis 45 degrees. Note how this does not
        change the location of the underlying dataset.

        >>> import pyvista as pv
        >>> mesh = pv.Cube()
        >>> pl = pv.Plotter()
        >>> _ = pl.add_mesh(mesh, color='b')
        >>> actor = pl.add_mesh(
        ...     mesh, color='r', style='wireframe', line_width=5, lighting=False,
        ... )
        >>> actor.rotate_y(45)
        >>> pl.show_axes()
        >>> pl.show()

        """
        self.RotateY(angle)

    def rotate_z(self, angle: float):
        """Rotate the actor about the z axis.

        Parameters
        ----------
        angle : float
            Angle to rotate the actor about the z axis in degrees.

        Examples
        --------
        Rotate the actor about the Z axis 45 degrees. Note how this does not
        change the location of the underlying dataset.

        >>> import pyvista as pv
        >>> mesh = pv.Cube()
        >>> pl = pv.Plotter()
        >>> _ = pl.add_mesh(mesh, color='b')
        >>> actor = pl.add_mesh(
        ...     mesh, color='r', style='wireframe', line_width=5, lighting=False,
        ... )
        >>> actor.rotate_z(45)
        >>> pl.show_axes()
        >>> pl.show()

        """
        self.RotateZ(angle)

    @property
    def orientation(self) -> tuple:
        """Return or set the actor orientation.

        Orientation is defined as the rotation from the global axes in degrees
        about the actor's x, y, and z axes.

        Examples
        --------
        Show that the orientation changes with rotation.

        >>> import pyvista as pv
        >>> mesh = pv.Cube()
        >>> pl = pv.Plotter()
        >>> actor = pl.add_mesh(mesh)
        >>> actor.rotate_x(90)
        >>> actor.orientation  # doctest:+SKIP
        (90, 0, 0)

        Set the orientation directly.

        >>> actor.orientation = (0, 45, 45)
        >>> actor.orientation  # doctest:+SKIP
        (0, 45, 45)

        Reorient just the actor and plot it. Note how the actor is rotated
        about its own axes as defined by its position.

        >>> import pyvista as pv
        >>> mesh = pv.Cube()
        >>> pl = pv.Plotter()
        >>> _ = pl.add_mesh(mesh, color='b')
        >>> actor = pl.add_mesh(
        ...     mesh, color='r', style='wireframe', line_width=5, lighting=False,
        ... )
        >>> actor.position = (0, 0, 1)
        >>> actor.orientation = (45, 0, 0)
        >>> pl.show_axes()
        >>> pl.show()

        """
        return self.GetOrientation()

    @orientation.setter
    def orientation(self, value: tuple):
        self.SetOrientation(value)

    @property
    def bounds(self) -> tuple:
        """Return the bounds of the actor.

        Bounds are ``(-X, +X, -Y, +Y, -Z, +Z)``

        Examples
        --------
        >>> import pyvista as pv
        >>> pl = pv.Plotter()
        >>> mesh = pv.Cube(x_length=0.1, y_length=0.2, z_length=0.3)
        >>> actor = pl.add_mesh(mesh)
        >>> actor.bounds
        (-0.05, 0.05, -0.1, 0.1, -0.15, 0.15)

        """
        return self.GetBounds()

    @property
    def center(self) -> tuple:
        """Return the center of the actor.

        Examples
        --------
        >>> import pyvista as pv
        >>> pl = pv.Plotter()
        >>> actor = pl.add_mesh(pv.Sphere(center=(0.5, 0.5, 1)))
        >>> actor.center  # doctest:+SKIP
        (0.5, 0.5, 1)
        """
        return self.GetCenter()