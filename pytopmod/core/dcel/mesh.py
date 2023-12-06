import dataclasses
from typing import Generator

from pytopmod.core.edge import EdgeKey
from pytopmod.core.face import FaceKey
from pytopmod.core.keystore import KeyStore
from pytopmod.core.mesh import Mesh
from pytopmod.core.vertex import VertexKey


@dataclasses.dataclass(slots=True)
class EdgeNode:
  """An Edge Node in the DCEL structure."""
  vertex_1: VertexKey
  vertex_2: VertexKey
  face_1: FaceKey
  face_2: FaceKey
  vertex_1_next: EdgeKey
  vertex_2_next: EdgeKey

  def __repr__(self) -> str:
    return dataclasses.astuple(self).__repr__()


@dataclasses.dataclass(slots=True)
class DCELMesh(Mesh):
  """DCEL-backed Mesh class.

  This structure uses a map of EdgeNodes.

  Manifold-preserving operators are implemented in 'operators.py'.
  """
  edges: KeyStore[EdgeKey] = dataclasses.field(init=False)
  edge_nodes: dict[EdgeKey, EdgeNode] = dataclasses.field(init=False)

  def __post_init__(self):
    super(DCELMesh, self).__post_init__()
    self.edges = KeyStore[EdgeKey]('e')
    self.edge_nodes = {}

  def create_edge(
          self,
          vertex_1: VertexKey, vertex_2: VertexKey,
          face_1: FaceKey, face_2: FaceKey,
          vertex_1_next: EdgeKey, vertex_2_next: EdgeKey
  ) -> EdgeKey:
    edge = self.edges.new()
    self.edge_nodes[edge] = EdgeNode(
        vertex_1, vertex_2, face_1, face_2, vertex_1_next, vertex_2_next)
    return edge

  def delete_edge(self, edge: EdgeKey):
    return self.edges.delete(edge)

  def vertex_edges(self, vertex: VertexKey) -> Generator[EdgeKey, None, None]:
    """Returns a generator over the edges incident to a vertex."""
    for edge, node in self.edge_nodes.items():
      if vertex in (node.vertex_1, node.vertex_2):
        yield edge

  def face_edges(self, face: FaceKey) -> Generator[EdgeKey, None, None]:
    """Returns a generator over the edges on the boundary of a face."""
    for edge, node in self.edge_nodes.items():
      if face in (node.face_1, node.face_2):
        yield edge
