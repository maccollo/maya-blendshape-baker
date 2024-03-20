from maya import cmds
def get_blendshape_target_names(blendshape_node):
    targets = cmds.listAttr(blendshape_node + '.w', multi=True)
    targetNames = []

    for target in targets:
        targetNames.append(target)
    return targetNames

def get_blendShape_target_connections(blendshape_node):
    targets = cmds.listAttr(blendshape_node + '.w', multi=True)
    target_connection_in = []
    target_connection_out = []
    for target in targets:
        incoming = cmds.listConnections(blendshape_node + '.' + target, source=True, destination=False, plugs=True)
        outgoing = cmds.listConnections(blendshape_node + '.' + target, source=False, destination=True, plugs=True)
        target_connection_in.append(incoming)
        target_connection_out.append(outgoing)
    return target_connection_in, target_connection_out

def break_blendShape_target_connections(blendshape_node):   
    targets = cmds.listAttr(blendshape_node + '.w', multi=True)
    for target in targets:
        incoming = cmds.listConnections(blendshape_node + '.' + target, source=True, destination=False, plugs=True)
        outgoing = cmds.listConnections(blendshape_node + '.' + target, source=False, destination=True, plugs=True)
        if incoming:
            for conn in incoming:
                cmds.disconnectAttr(conn, blendshape_node + '.' + target)
        if outgoing:
            for conn in outgoing:
                cmds.disconnectAttr(blendshape_node + '.' + target, conn)
def zero_blendsShape_target_weights(blendshape_node):   
    targets = cmds.listAttr(blendshape_node + '.w', multi=True)
    for target in targets:
        cmds.setAttr(blendshape_node + '.' + target, 0)
def bake_blendshape_painted_weights(blendshape_node):
    base_mesh = get_base_shape_from_blendshape(blendshape_node)
    target_names = get_blendshape_target_names(blendshape_node)
    target_connections_in, target_conections_out = get_blendShape_target_connections(blendshape_node)
    break_blendShape_target_connections(blendshape_node)
    zero_blendsShape_target_weights(blendshape_node)
    shapes_and_weights = duplicate_shapes(blendshape_node,target_names, base_mesh)
    recreate_blendshape(blendshape_node,base_mesh, target_names, shapes_and_weights,target_connections_in)
def recreate_blendshape(blendshape_node,base_mesh, target_names, shapes_and_weights,target_connections_in):
    cmds.delete(blendshape_node)
    new_blendshape = cmds.blendShape(base_mesh, name=blendshape_node)
    for i, shape_tuple in enumerate(shapes_and_weights):
        full_shape = shape_tuple[2]
        print(full_shape)
        inbetween_shapes = shape_tuple[0]
        inbetween_weights = shape_tuple[1]
        print(i)
        cmds.blendShape(new_blendshape, e=True, target=(base_mesh, i, full_shape, 1.0))
        cmds.delete(full_shape)
        for weight, shape in zip(inbetween_weights, inbetween_shapes):
            print(weight, shape)
            cmds.blendShape(new_blendshape, e=True, target=(base_mesh, i, shape, weight), inBetween=True)
            cmds.delete(shape)
        rename_blendshape_target(blendshape_node, full_shape, target_names[i]) 
        #reconnect the connections
        conn = target_connections_in[i]
        if conn:
            for connection in conn:
                cmds.connectAttr(connection, blendshape_node + '.' + target_names[i])
def duplicate_shapes(blendshape_node,targets,base_mesh):
    shapes_and_weights = []
    for target in targets:
        weights,_,_,_ = find_inbetween_weights_from_target_name(blendshape_node, target)
        print(weights)
        shapes = []
        for weight in weights:
            cmds.setAttr(blendshape_node + '.' + target, weight)
            if weight == 1.0:
                continue
            duplicated_mesh = cmds.duplicate(base_mesh)[0]
            shapes.append(duplicated_mesh)
        
        cmds.setAttr(blendshape_node + '.' + target, 1)
        duplicated_mesh=cmds.duplicate(base_mesh)[0]
        cmds.setAttr(blendshape_node + '.' + target, 0)
        shapes_and_weights.append((shapes,weights,duplicated_mesh))
    return shapes_and_weights
    
def find_inbetween_weights_from_target_name(blendshape_node, target_name):
    """Finds and returns the inbetween weights, inbetween items (inbetween index for the node) and target index of a blendshape target"""
    target_index = get_blendshape_target_index(blendshape_node, target_name)
    if target_index is not None:
        inbetween_weights, inbetween_items,target_item = find_inbetween_weights_from_target_index(blendshape_node, target_index)
        if inbetween_weights:
            return inbetween_weights, inbetween_items,target_item,target_index
    return None
def get_blendshape_target_index(blendshape_node, target_name):
    """
    Takes the name of a blendshape target and returns the index.
    """
    alias_list = cmds.aliasAttr(blendshape_node, q=True)
    target_index = None
    for i, alias in enumerate(alias_list):
        if alias == target_name:
            target_index = i // 2  # Each target has two entries in the alias list (weight and input)
            return target_index
    #rise error if the target is not found
    raise ValueError(f"Target {target_name} not found in blendshape node {blendshape_node}.")

def find_inbetween_weights_from_target_index(blendshape_node, target_index):
    """
    Attempt to find the inbetween weights for a specific target of a blendshape node by checking each
    inputTargetItem for available inbetween weights.
    """
    inbetween_weights = []
    inbetween_items = []
    # Attempt to query all inputTargetItems for the targetIndex
    target_items = cmds.getAttr(f'{blendshape_node}.inputTarget[0].inputTargetGroup[{target_index}].inputTargetItem', multiIndices=True)
    
    if target_items:
        for item in target_items:
            weight = (item - 5000) / 1000.0  # Convert the internal weight to the actual weight
            if True or 0 < weight and weight < 1:
                inbetween_weights.append(weight)
                inbetween_items.append(item)
            if weight == 1:
                target_item = item
    
    return inbetween_weights, inbetween_items, target_item

def get_base_shape_from_blendshape(blendshape_node):
    """
    Retrieves the base shape connected to the specified blendshape node.
    """
    # Find the geometry connected as input to the blendshape node
    connections = cmds.listConnections(blendshape_node + '.outputGeometry', source=False, destination=True)
    if connections:
        #check if the connection is a shape node
        for connection in connections:
            if cmds.nodeType(connection) == 'transform':
                return connection
            else:
                #If not we continue to the next connection
                return get_base_shape_from_blendshape(connection)

    else:
        cmds.warning("No base shape found for blendshape node: " + blendshape_node)
        return None
    
def rename_blendshape_target(bls, old_alias, new_alias):
    '''
    rename_blendshape_target('C_baseShape_BLS', 'C_eyebrowUp_PLY', 'C_eyebrowDown_PLY')
    '''
    all_aliases = cmds.aliasAttr(bls, q=True) 
    # format: ['alias0', 'weight[0]', 'alias1', 'weight[1]']
    if not old_alias in all_aliases:
        raise ValueError(
            "BlendShape node '{bls}' doesn't have an alias '{old_alias}'".format(**locals()))
    old_alias_attr_index = all_aliases.index(old_alias) + 1
    old_alias_attr = all_aliases[old_alias_attr_index]
    cmds.aliasAttr(new_alias, '{bls}.{old_alias_attr}'.format(**locals()))