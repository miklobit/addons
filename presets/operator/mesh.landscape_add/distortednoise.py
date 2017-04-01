import bpy
op = bpy.context.active_operator

op.AutoUpdate = True
op.SphereMesh = False
op.SmoothMesh = True
op.Subdivision = 128
op.MeshSize = 2.0
op.XOffset = 0.0
op.YOffset = 0.0
op.RandomSeed = 13
op.NoiseSize = 1.0
op.NoiseType = 'variable_lacunarity'
op.BasisType = '0'
op.VLBasisType = '3'
op.Distortion = 1.5
op.HardNoise = False
op.NoiseDepth = 8
op.mDimension = 1.0
op.mLacunarity = 2.0
op.mOffset = 1.0
op.mGain = 1.0
op.MarbleBias = '0'
op.MarbleSharp = '0'
op.MarbleShape = '0'
op.Invert = True
op.Height = 0.10999999940395355
op.Offset = 0.029999999329447746
op.Falloff = '1'
op.Sealevel = 0.0
op.Plateaulevel = 1.0
op.Strata = 5.0
op.StrataType = '0'