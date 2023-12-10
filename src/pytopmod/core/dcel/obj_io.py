"""Conversion functions between OBJ format and DCEL representation."""
from pytopmod.core.dcel import operators
from pytopmod.core.dcel.mesh import DCELMesh


def mesh_to_obj(mesh: DCELMesh) -> str:
  """Converts a DCELMesh to OBJ format."""
  vertex_map = {}

  obj_vertices = []
  for index, vertex in enumerate(mesh.vertices):
    vertex_map[vertex] = index
    coordinates = (str(coord) for coord in mesh.vertex_coordinates[vertex])
    obj_vertices.append(f'v {" ".join(coordinates)}')

  obj_faces = []
  for face in mesh.faces:
    edges = list(operators.face_trace(mesh, face))
    vertex_pairs = []

    for i in range(len(edges) - 1):
      edge_node_1 = mesh.edge_nodes[edges[i]]
      edge_node_2 = mesh.edge_nodes[edges[i+1]]
      vertex_pairs.append(
          (edge_node_1.vertex_1, edge_node_1.vertex_2)
          if edge_node_1.vertex_2 in (
              edge_node_2.vertex_1, edge_node_2.vertex_2)
          else (edge_node_1.vertex_2, edge_node_1.vertex_1))

    vertices = [pair[0] for pair in vertex_pairs] + [vertex_pairs[-1][-1]]

    indices = list(str(vertex_map[vertex] + 1) for vertex in vertices)
    obj_faces.append(f'f {" ".join(indices)}')

  return '\n'.join(obj_vertices) + '\n' + '\n'.join(obj_faces)
