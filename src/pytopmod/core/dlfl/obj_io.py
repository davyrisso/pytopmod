"""Conversion functions between OBJ format and DLFL representation."""
from pytopmod.core.dlfl.mesh import DLFLMesh


def mesh_to_obj(mesh: DLFLMesh) -> str:
  """Converts a DLFLMesh to OBJ format."""
  vertex_index_map = {}

  obj_vertices = []
  for index, vertex in enumerate(mesh.vertices):
    vertex_index_map[vertex] = index
    coordinates = (str(coord) for coord in mesh.vertex_coordinates[vertex])
    obj_vertices.append(f'v {" ".join(coordinates)}')

  obj_faces = []
  for face in mesh.faces:
    indices = (str(vertex_index_map[vertex] + 1)
               for vertex in mesh.face_vertices[face])
    obj_faces.append(f'f {" ".join(indices)}')

  return '\n'.join(obj_vertices) + '\n' + '\n'.join(obj_faces)


def obj_to_mesh(obj: str) -> DLFLMesh:
  raise NotImplementedError()
