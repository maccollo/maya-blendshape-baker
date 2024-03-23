# maya-blendshape-baker
This is a tool that converts a blendshape node in maya which may have painted target weights and inbetweens into a blendnode that is compatible with unreal engine.
First this is done by duplicating the shape at for every target, including inbetween weights, and using that as a new target in a new blendshape node. This bakes the result of painted weights into the new targets.
Second, the driver of the original target weight is connected to the new target. With inbetween targets this is done in such a way that the same motion is produced.



https://github.com/maccollo/maya-blendshape-baker/assets/23036010/5b4559bd-a887-4d00-a636-2482add40121

