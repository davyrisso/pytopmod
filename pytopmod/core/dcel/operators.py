"""Manifold-preserving operators on DCEL Meshes."""
import itertools
from typing import Generator, Optional

from pytopmod.core.dcel.mesh import DCELMesh
from pytopmod.core.edge import EdgeKey
from pytopmod.core.face import FaceKey
from pytopmod.core.vertex import VertexKey


def vertex_trace(
        mesh: DCELMesh,
        vertex: VertexKey,
        start_edge: Optional[EdgeKey] = None) -> Generator[EdgeKey, None, None]:
  """Returns a generator over the edges that form a vertex rotation.

  The starting edge can optionally be specified, otherwise one will be picked.
  """
  first_edge = start_edge or next(mesh.vertex_edges(vertex))
  if first_edge is None:
    return
  yield first_edge

  node = mesh.edge_nodes[first_edge]
  edge = node.vertex_1_next if node.vertex_1 == vertex else node.vertex_2_next

  while edge != first_edge:
    yield edge
    node = mesh.edge_nodes[edge]
    edge = node.vertex_1_next if node.vertex_1 == vertex else node.vertex_2_next


def face_trace(
        mesh: DCELMesh,
        face: FaceKey,
        start_edge: Optional[EdgeKey] = None) -> Generator[EdgeKey, None, None]:
  """Returns a generator over the edges that form a face boundary.

  The starting edge can optionally be specified, otherwise one will be picked.
  """
  first_edge = start_edge or next(mesh.face_edges(face))
  if first_edge is None:
    return
  yield first_edge

  node = mesh.edge_nodes[first_edge]
  edge = node.vertex_1_next if node.face_1 == face else node.vertex_2_next

  while edge != first_edge:
    yield edge
    node = mesh.edge_nodes[edge]
    edge = node.vertex_1_next if node.face_1 == face else node.vertex_2_next


def insert_edge(
        mesh: DCELMesh,
        vertex_1: VertexKey, edge_1: EdgeKey,
        vertex_2: VertexKey, edge_2: EdgeKey):
  """Inserts an edge between two corners.

  If the two corners:
    - belong to the same face, the face will be split into two new ones.
    - belong to two different faces, the faces will be merged into a new one.
  """
  edge_1_node = mesh.edge_nodes[edge_1]
  edge_2_node = mesh.edge_nodes[edge_2]

  # 1.1 - Find the 2nd edges for each corner.
  edge_1_2 = (edge_1_node.vertex_1_next if edge_1_node.vertex_1 == vertex_1
              else edge_1_node.vertex_2_next)
  edge_2_2 = (edge_2_node.vertex_1_next if edge_2_node.vertex_1 == vertex_2
              else edge_2_node.vertex_2_next)

  # 1.2 - Find the faces that contain each corner.
  face_1 = (edge_1_node.face_1 if edge_1_node.vertex_1 ==
            vertex_1 else edge_1_node.face_2)
  face_2 = (edge_2_node.face_1 if edge_2_node.vertex_1 ==
            vertex_2 else edge_1_node.face_2)

  # Set the vertex and edge information for the new edge.
  # 2 - Create a new edge node.
  new_edge = mesh.create_edge(
      vertex_1, vertex_2,
      face_1, face_2,
      edge_1_2, edge_2_2)
  new_edge_node = mesh.edge_nodes[new_edge]

  # Non-cofacial insertion.
  if face_1 != face_2:
    # 3.1 - Update the face information.
    # Create a new face.
    new_face = mesh.create_face()
    # Traverse the corners' faces and replace face_1 and face_2 by the new face.
    for edge in list(itertools.chain(face_trace(mesh, face_1),
                                     face_trace(mesh, face_2))):
      node = mesh.edge_nodes[edge]
      if node.face_1 in (face_1, face_2):
        node.face_1 = new_face
      if node.face_2 in (face_1, face_2):
        node.face_2 = new_face
    # Set the face information for the new edge.
    new_edge_node.face_1 = new_face
    new_edge_node.face_2 = new_face
    # Delete the old faces.
    mesh.delete_face(face_1)
    mesh.delete_face(face_2)

    # 3.2 - Update the edge information.
    if edge_1_node.vertex_1 == vertex_1:
      edge_1_node.vertex_1_next = new_edge
    else:
      edge_1_node.vertex_2_next = new_edge
    if edge_2_node.vertex_1 == vertex_2:
      edge_2_node.vertex_1_next = new_edge
    else:
      edge_2_node.vertex_2_next = new_edge

  # Cofacial insertion.
  else:
    # 4.1 - Update the edge information.
    if edge_1_node.vertex_1 == vertex_1:
      edge_1_node.vertex_1_next = new_edge
    else:
      edge_1_node.vertex_2_next = new_edge
    if edge_2_node.vertex_1 == vertex_2:
      edge_2_node.vertex_1_next = new_edge
    else:
      edge_2_node.vertex_2_next = new_edge

    # 4.2 - Update the face information.
    # Create two new faces.
    new_face_1 = mesh.create_face()
    new_face_2 = mesh.create_face()

    # Starting from one direction of the new edge, replace face_1 by new_face_1.
    for edge in list(face_trace(mesh, face_1, start_edge=edge_1_2)):
      edge_node = mesh.edge_nodes[edge]
      if edge_node.face_1 == face_1:
        edge_node.face_1 = new_face_1
      else:
        edge_node.face_2 = new_face_1

    # Starting from the opposite direction, replace face_1 by new_face_2.
    for edge in list(face_trace(mesh, face_1, start_edge=edge_2_2)):
      edge_node = mesh.edge_nodes[edge]
      if edge_node.face_1 == face_1:
        edge_node.face_1 = new_face_2
      else:
        edge_node.face_2 = new_face_2

    # Delete face_1 == face_2.
    mesh.delete_face(face_1)


def delete_edge(mesh: DCELMesh, old_edge: EdgeKey):
  old_edge_node = mesh.edge_nodes[old_edge]

  # 1.1 - Find the edges before and after the edge in the rotation of vertex_1.
  vertex_1_rotation = list(vertex_trace(mesh, old_edge_node.vertex_1))
  vertex_1_previous = vertex_1_rotation[
      vertex_1_rotation.index(old_edge) - 1 % len(vertex_1_rotation)]
  vertex_1_previous_node = mesh.edge_nodes[vertex_1_previous]
  vertex_1_next = vertex_1_rotation[
      vertex_1_rotation.index(old_edge) + 1 % len(vertex_1_rotation)]

  # 1.2 - Find the edges before and after the edge in the rotation of vertex_2.
  vertex_2_rotation = list(vertex_trace(mesh, old_edge_node.vertex_2))
  vertex_2_previous = vertex_2_rotation[
      vertex_2_rotation.index(old_edge) - 1 % len(vertex_2_rotation)]
  vertex_2_previous_node = mesh.edge_nodes[vertex_2_previous]
  vertex_2_next = vertex_2_rotation[
      vertex_2_rotation.index(old_edge) + 1 % len(vertex_2_rotation)]

  face_1 = old_edge_node.face_1
  face_2 = old_edge_node.face_2

  # 2 - Non-cofacial deletion.
  if face_1 != face_2:
    # 2.1 - Update the face information.
    # Create a new face.
    new_face = mesh.create_face()

    # Traverse face_1 and face_2, replace face_1 and face_2 with new_face.
    for edge in list(itertools.chain(
            face_trace(mesh, face_1), face_trace(mesh, face_2))):
      edge_node = mesh.edge_nodes[edge]
      if edge_node.face_1 in (face_1, face_2):
        edge_node.face_1 = new_face
      if edge_node.face_2 in (face_1, face_2):
        edge_node.face_2 = new_face

    # Delete face_1 and face_2.
    mesh.delete_face(face_1)
    mesh.delete_face(face_2)

    # 2.2 - Update the edge information to delete the edge.
    if vertex_1_previous_node.vertex_1 == old_edge_node.vertex_1:
      vertex_1_previous_node.vertex_1_next = vertex_1_next
    else:
      vertex_1_previous_node.vertex_2_next = vertex_1_next
    if vertex_2_previous_node.vertex_1 == old_edge_node.vertex_2:
      vertex_2_previous_node.vertex_1_next = vertex_2_next
    else:
      vertex_2_previous_node.vertex_2_next = vertex_2_next

    # Delete the edge.
    mesh.delete_edge(old_edge)

  # 3 - Cofacial deletion.
  else:
    # 3.1 - Update the edge information to delete the edge.
    if vertex_1_previous_node.vertex_1 == old_edge_node.vertex_1:
      vertex_1_previous_node.vertex_1_next = vertex_1_next
    else:
      vertex_1_previous_node.vertex_2_next = vertex_1_next
    if vertex_2_previous_node.vertex_1 == old_edge_node.vertex_2:
      vertex_2_previous_node.vertex_1_next = vertex_2_next
    else:
      vertex_2_previous_node.vertex_2_next = vertex_2_next

    # Delete the edge.
    mesh.delete_edge(old_edge)

    # 3.2 - Update the face information.
    # Create two new faces.
    new_face_1 = mesh.create_face()
    new_face_2 = mesh.create_face()

    # Starting from vertex_1_previous, traverse the face and replace face_1 by
    # new_face_1.
    for edge in list(face_trace(mesh, face_1, start_edge=vertex_1_previous)):
      edge_node = mesh.edge_nodes[edge]
      if edge_node.face_1 == face_1:
        edge_node.face_1 = new_face_1
      if edge_node.face_2 == face_1:
        edge_node.face_2 == face_1

    # Starting from vertex_2_previous, traverse the face and replace face_1 by
    # new_face_2.
    for edge in list(face_trace(mesh, face_1, start_edge=vertex_2_previous)):
      edge_node = mesh.edge_nodes[edge]
      if edge_node.face_1 == face_1:
        edge_node.face_1 = new_face_2
      if edge_node.face_2 == face_1:
        edge_node.face_2 = new_face_2

    # Delete face_1 == face_2.
    mesh.delete_face(face_1)
