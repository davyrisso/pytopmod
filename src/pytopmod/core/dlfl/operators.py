"""Manifold-preserving operators on DLFL Meshes."""
from typing import Generator, Tuple, cast

from pytopmod.core import circular_list
from pytopmod.core.dlfl.mesh import DLFLMesh
from pytopmod.core.face import FaceKey
from pytopmod.core.geometry import Point3D
from pytopmod.core.half_edge import HalfEdge
from pytopmod.core.vertex import VertexKey


def face_trace(
        mesh: DLFLMesh, face: FaceKey) -> Generator[HalfEdge, None, None]:
  """Returns a generator over the half-edges of a face boundary."""
  # Simply form half-edges from the pairs of vertices in a face boundary.
  return (
      HalfEdge(vertex_pair, face)
      for vertex_pair in circular_list.pairs(mesh.face_vertices[face]))


def vertex_trace(
        mesh: DLFLMesh, vertex: VertexKey) -> (Generator[HalfEdge, None, None]):
  """Returns a generator over the half-edges of a vertex rotation."""
  # Pick a first face in the set of the vertex's faces rotation.
  first_face = next(iter(mesh.vertex_faces[vertex]))
  # Output the first half-edge formed by the passed vertex and its successor
  # in the picked face's boundary: [u, v].
  first_half_edge = HalfEdge((vertex, circular_list.next_item(
      mesh.face_vertices[first_face], vertex)), first_face)
  yield first_half_edge

  # Find the face in the vertex rotation that contains the opposite half-edge.
  face = next(
      key for key in mesh.vertex_faces[first_half_edge.vertices[1]]
      if (first_half_edge.vertices[1], first_half_edge.vertices[0])
      in circular_list.pairs(mesh.face_vertices[key]))

  half_edge = HalfEdge(
      (first_half_edge.vertices[1], first_half_edge.vertices[0]), face)

  while half_edge != first_half_edge:
    yield half_edge
    if half_edge.vertices[1] == vertex:
      # If the current half-edge's tail vertex is the passed vertex, form the
      # next half-edge from the passed vertex and its successor in the current
      # face.
      half_edge = HalfEdge(
          (half_edge.vertices[1],
           circular_list.next_item(
              mesh.face_vertices[face], half_edge.vertices[1])),
          face)
    else:
      # If the current half-edge's head is the passed vertex, find the face in
      # the passed vertex rotation that contains the opposite half-edge.
      face = next(
          key for key in mesh.vertex_faces[half_edge.vertices[1]]
          if (half_edge.vertices[1], half_edge.vertices[0])
          in circular_list.pairs(mesh.face_vertices[key]))
      half_edge = HalfEdge(
          (half_edge.vertices[1], half_edge.vertices[0]), face)


def create_point_sphere(
        mesh: DLFLMesh, position: Point3D) -> Tuple[VertexKey, FaceKey]:
  """Creates a point-sphere in the passed mesh.

  Creates a face and a vertex at the passed position, set the vertex as the
  only element in the created face's boundary, and set the face as the only
  element in the created vertex's face rotation.
  """
  vertex = mesh.create_vertex(position)
  face = mesh.create_face()
  mesh.face_vertices[face].append(vertex)
  mesh.vertex_faces[vertex].add(face)
  return (vertex, face)


def insert_edge(
    mesh: DLFLMesh,
    vertex_1: VertexKey, face_1: FaceKey,
    vertex_2: VertexKey, face_2: FaceKey
) -> Tuple[FaceKey, FaceKey]:
  """Inserts an edge between two corners.

  Returns the faces created as a result of this operation: 
   - A tuple of (new_face_1, new_face_2) for a cofacial insertion.
   - A tuple of (new_face, new_face) for a non-cofacial insertion.
  """
  return (_insert_edge_cofacial if face_1 == face_2
          else _insert_edge_non_cofacial
          )(mesh, vertex_1,  face_1, vertex_2, face_2)


def _insert_edge_cofacial(
    mesh: DLFLMesh,
    vertex_1: VertexKey, old_face: FaceKey,
    vertex_2: VertexKey, _: FaceKey
) -> Tuple[FaceKey, FaceKey]:
  """Inserts an edge between two corners in the same face.

  This will split the old face into two new ones.
  """
  # Create two new faces.
  new_face_1 = mesh.create_face()
  new_face_2 = mesh.create_face()

  # Compute the boundaries of the newly created faces as the boundary of the old
  # face circulated to end with vertex_2 and split at vertex_1.
  new_face_1_vertices, new_face_2_vertices = (
      circular_list.split_at_item(
          circular_list.circulated_to_item(
              mesh.face_vertices[old_face], vertex_2), vertex_1))

  # Append vertex_2 to new_face_1's boundary (resp. vertex_1 to new_face_2).
  mesh.face_vertices[new_face_1] = new_face_1_vertices + [vertex_2]
  mesh.face_vertices[new_face_2] = new_face_2_vertices + [vertex_1]

  # Update the vertices face rotations:
  # Replace old_face with new_face_1 for each vertex in new_face_1.
  for vertex_key in mesh.face_vertices[new_face_1]:
    mesh.vertex_faces[vertex_key].discard(old_face)
    mesh.vertex_faces[vertex_key].add(new_face_1)

  # Replace old_face with new_face_2 for each vertex in new_face_2.
  for vertex_key in mesh.face_vertices[new_face_2]:
    mesh.vertex_faces[vertex_key].discard(old_face)
    mesh.vertex_faces[vertex_key].add(new_face_2)

  # Delete the old face.
  mesh.delete_face(old_face)

  return (new_face_1, new_face_2)


def _insert_edge_non_cofacial(
    mesh: DLFLMesh,
    vertex_1: VertexKey, old_face_1: FaceKey,
    vertex_2: VertexKey, old_face_2: FaceKey
) -> Tuple[FaceKey, FaceKey]:
  """Inserts an edge between two corners of two different faces.

  This will merge the two old faces into a new one.
  """
  # Create a new face.
  new_face = mesh.create_face()

  old_face_1_vertices = mesh.face_vertices[old_face_1]
  old_face_2_vertices = mesh.face_vertices[old_face_2]

  # Compute the boundary of the newly created face as the concatenation of:
  #  - old_face_1's boundary circulated to end with vertex_1
  #  - old_face_2's boundary circulated to end with vertex_2's predecessor.
  #  - vertex_2 if old face 2 was not a point-sphere.
  #  - vertex_2 if old_face_1 was not a point-sphere.
  new_face_vertices = (
      circular_list.circulated_to_item(old_face_1_vertices, vertex_1) +
      circular_list.circulated_to_item(
          old_face_2_vertices,
          circular_list.previous_item(old_face_2_vertices, vertex_2)) +
      ([vertex_2] if len(old_face_2_vertices) > 1 else []) +
      ([vertex_1] if len(old_face_1_vertices) > 1 else []))
  mesh.face_vertices[new_face] = new_face_vertices

  # Update the vertices face rotations:
  for vertex in new_face_vertices:
    # Replace old_face_1 and old_face_2 with the new_face for each vertex.
    mesh.vertex_faces[vertex].discard(old_face_1)
    mesh.vertex_faces[vertex].discard(old_face_2)
    mesh.vertex_faces[vertex].add(new_face)

  # Delete the old faces.
  mesh.delete_face(old_face_1)
  mesh.delete_face(old_face_2)

  return (new_face, new_face)


def delete_edge(
    mesh: DLFLMesh,
    vertex_1: VertexKey, face_1: FaceKey,
    vertex_2: VertexKey, face_2: FaceKey
) -> Tuple[FaceKey, FaceKey]:
  """Deletes an edge between two corners.

  Returns the faces created as a result of this operation:
   - A tuple of (new_face_1, new_face_2) for a cofacial deletion.
   - A tuple of (new_face, new_face) for a non-cofacial deletion.
  """
  return (_delete_edge_cofacial if face_1 == face_2
          else _delete_edge_non_cofacial
          )(mesh, vertex_1,  face_1, vertex_2, face_2)


def _delete_edge_cofacial(
    mesh: DLFLMesh,
    vertex_1: VertexKey, old_face: FaceKey,
    vertex_2: VertexKey, _: FaceKey
) -> Tuple[FaceKey, FaceKey]:
  """Deletes an edge between two corners of the same face.

  This will split the old face into two new ones.
  """
  # Create two new faces.
  new_face_1 = mesh.create_face()
  new_face_2 = mesh.create_face()

  # Compute the boundaries of the new faces as the boundary of the old face
  # circulated to (vertex_1, vertex_2) and split at (vertex_2, vertex_1).
  new_face_1_vertices, new_face_2_vertices = (
      circular_list.split_at_pair(
          circular_list.circulated_to_pair(
              mesh.face_vertices[old_face], (vertex_1, vertex_2)),
          (vertex_2, vertex_1)))

  # Remove the last vertices from the created faces (i.e vertex_1 and vertex_2).
  mesh.face_vertices[new_face_1] = new_face_1_vertices[:-1]
  mesh.face_vertices[new_face_2] = new_face_2_vertices[:-1]

  # Update the vertices face rotations:
  for vertex in mesh.face_vertices[new_face_1]:
    # Replace old_face with new_face_1 for each vertex in new_face_1.
    mesh.vertex_faces[vertex].discard(old_face)
    mesh.vertex_faces[vertex].add(new_face_1)

  for vertex in mesh.face_vertices[new_face_2]:
    # Replace old_face with new_face_2 for each vertex in new_face_2.
    mesh.vertex_faces[vertex].discard(old_face)
    mesh.vertex_faces[vertex].add(new_face_2)

  # Delete the old face.
  mesh.delete_face(old_face)

  return (new_face_1, new_face_2)


def _delete_edge_non_cofacial(
    mesh: DLFLMesh,
    vertex_1: VertexKey, old_face_1: FaceKey,
    vertex_2: VertexKey, old_face_2: FaceKey
) -> Tuple[FaceKey, FaceKey]:
  """Deletes an edge between two corners of two different faces.

  This will merge the two old faces into a new one.
  """
  # Create a new face.
  new_face = mesh.create_face()

  old_face_1_vertices = mesh.face_vertices[old_face_1]
  old_face_2_vertices = mesh.face_vertices[old_face_2]

  # Compute the new face's boundary as the concatenation of:
  #  - old_face_1's boundary circulated to vertex_1, without vertex_1.
  #  - old_face_2's boundary circulated to vertex_2, without vertex_2.
  new_face_vertices = (
      circular_list.circulated_to_item(old_face_1_vertices, vertex_1)[:-1] +
      circular_list.circulated_to_item(old_face_2_vertices, vertex_2)[:-1])

  mesh.face_vertices[new_face] = new_face_vertices

  # Update the vertices face rotations:
  for vertex in new_face_vertices:
    # Replace old_face_1 and old_face_2 with new_face for each vertex of the
    # new face.
    mesh.vertex_faces[vertex].discard(old_face_1)
    mesh.vertex_faces[vertex].discard(old_face_2)
    mesh.vertex_faces[vertex].add(new_face)

  mesh.delete_face(old_face_1)
  mesh.delete_face(old_face_2)

  return (new_face, new_face)
