from pytopmod.core.dcel.mesh import DCELMesh


def tetrahedron() -> DCELMesh:
  mesh = DCELMesh()

  mesh.create_vertex((1, 1, 1))
  mesh.create_vertex((1, -1, -1))
  mesh.create_vertex((-1, 1, -1))
  mesh.create_vertex((-1, -1, 1))

  mesh.create_face()
  mesh.create_face()
  mesh.create_face()
  mesh.create_face()

  mesh.create_edge('v2', 'v1', 'f4', 'f1', 'e6', 'e3')
  mesh.create_edge('v1', 'v3', 'f4', 'f2', 'e1', 'e5')
  mesh.create_edge('v1', 'v4', 'f2', 'f1', 'e2', 'e4')
  mesh.create_edge('v4', 'v2', 'f3', 'f1', 'e5', 'e1')
  mesh.create_edge('v3', 'v4', 'f3', 'f2', 'e6', 'e3')
  mesh.create_edge('v2', 'v3', 'f3', 'f4', 'e4', 'e2')

  return mesh


def square() -> DCELMesh:
  mesh = DCELMesh()

  mesh.create_vertex((-1.0, 1.0, 0.0))
  mesh.create_vertex((1.0, 1.0, 0.0))
  mesh.create_vertex((1.0, -1.0, 0.0))
  mesh.create_vertex((-1.0, -1.0, 0))

  mesh.create_face()
  mesh.create_face()

  mesh.create_edge('v1', 'v2', 'f1', 'f2', 'e4', 'e2')
  mesh.create_edge('v2', 'v3', 'f1', 'f2', 'e1', 'e3')
  mesh.create_edge('v3', 'v4', 'f1', 'f2', 'e2', 'e4')
  mesh.create_edge('v4', 'v1', 'f1', 'f2', 'e3', 'e1')

  return mesh
