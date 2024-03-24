# maya-blendshape-baker
This is a tool that converts a blendshape node in maya which may have painted target weights and inbetweens into a blendnode that is compatible with unreal engine.
First this is done by duplicating the shape at for every target, including inbetween weights, and using that as a new target in a new blendshape node. This bakes the result of painted weights into the new targets.
Second, the driver of the original target weight is connected to the new target. With inbetween targets this is done in such a way that the same motion is produced.

Options:

  Unreal compatible inbetweens.
  
    If turned on each inbetween will be recreated as a target. A network of nodes will automatically be setup so the same behaviour is created from the driver attribute, as in the example video.
    
  Delete Original Node:
  
    Deletes the original blendshape node when checked.
    
  Create Dummy Target Drivers:
  
    If unreal compatible inbetweens is turned on, this will create zero deformation targets on the new blendshape node with the same names as in the original blendshape node. These act as driver attributes for the actual targets. If unchecked the driver attriute will be a float constant node.



https://github.com/maccollo/maya-blendshape-baker/assets/23036010/5b4559bd-a887-4d00-a636-2482add40121

