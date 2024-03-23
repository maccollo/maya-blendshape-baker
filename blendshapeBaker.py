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
def bake_blendshape_painted_weights(blendshape_node, make_unreal_compatible, delete_orignal_node):
    base_mesh = get_base_shape_from_blendshape(blendshape_node)
    target_names = get_blendshape_target_names(blendshape_node)
    target_connections_in, target_conections_out = get_blendShape_target_connections(blendshape_node)
    break_blendShape_target_connections(blendshape_node)
    zero_blendsShape_target_weights(blendshape_node)
    shapes_and_weights = duplicate_shapes(blendshape_node,target_names, base_mesh)
    recreate_blendshape(blendshape_node,base_mesh, target_names, shapes_and_weights,target_connections_in,UE_compatible_inbetweens = make_unreal_compatible,delete_original_node = delete_orignal_node)
    if not delete_orignal_node:
        reconnect_original_connections(blendshape_node, target_connections_in,target_names)

def reconnect_original_connections(blendshape_node, target_connections_in,targets):
    for connection_in, target in zip(target_connections_in,targets):
        if connection_in:
            for connection in connection_in:
                cmds.connectAttr(connection, blendshape_node + '.' + target)
    cmds.setAttr(blendshape_node + '.envelope', 0)


def recreate_blendshape(blendshape_node,base_mesh, target_names, shapes_and_weights,target_connections_in, UE_compatible_inbetweens=True, delete_original_node = False):
    if delete_original_node:
        cmds.delete(blendshape_node)
        
    new_blendshape = cmds.blendShape(base_mesh, name=blendshape_node+ '_Baked')[0]
    for i, shape_tuple in enumerate(shapes_and_weights):
        full_shape = shape_tuple[2]
        inbetween_shapes = shape_tuple[0]
        inbetween_weights = shape_tuple[1]
        conn = target_connections_in[i]
        if not UE_compatible_inbetweens:
            cmds.blendShape(new_blendshape, e=True, target=(base_mesh, i, full_shape, 1.0))
            cmds.delete(full_shape)
            for weight, shape in zip(inbetween_weights, inbetween_shapes):
                if weight == 1.0:
                    continue
                cmds.blendShape(new_blendshape, e=True, target=(base_mesh, i, shape, weight), inBetween=True)
                cmds.delete(shape)
            rename_blendshape_target(new_blendshape, full_shape, target_names[i]) 
        #reconnect the connections
        
            if conn:
                for connection in conn:
                    cmds.connectAttr(connection, new_blendshape + '.' + target_names[i])
        else:
            #insert 0 in the weights list. Go through the list and if the next weight value is positive insert 0 at the current index. Also insert an empty string in the shapes list

            for j in range(len(inbetween_weights)):
                if inbetween_weights[j] > 0:
                    inbetween_weights.insert(j,0.0)
                    inbetween_shapes.insert(j,'')
                    break
            for j,(weight, shape) in enumerate(zip(inbetween_weights,inbetween_shapes)):
                if weight == 0.0:
                    continue
                target_name = target_names[i] + '_' + str(round(1000*weight))
                add_blendshape_target_with_name(new_blendshape,base_mesh,shape,target_name)
                if len(inbetween_weights) < 2:
                    raise ValueError("Shape length is less than two. Something went wrong. Weights and shapes: {inbetween_weights} {inbetween_shapes}")
                w_a = inbetween_weights[j-1] if j>0 else inbetween_weights[j+1]
                w_b = inbetween_weights[j]
                w_c = inbetween_weights[j+1] if j+1 < len(inbetween_weights) else inbetween_weights[j-1]
                if conn:
                    driver_input = conn[0]
                    output = create_inbetweener_driver(w_a,w_b,w_c,driver_input, second_first= j == 1, second_last=j == len(inbetween_weights)-2)
                    cmds.connectAttr(output, new_blendshape + '.' + target_name)
                cmds.delete(shape)
            cmds.delete(full_shape)

def add_blendshape_target_with_name(blendshape_node,base_mesh,target_mesh, name):
    """Adds a blendshape target and gives it the specified name"""
    first_target = get_number_of_blendshape_targets(blendshape_node) == 0
    old_aliases = cmds.aliasAttr(blendshape_node, q=True) if not first_target else []
    cmds.blendShape(blendshape_node, edit=True, target=(base_mesh, get_number_of_blendshape_targets(blendshape_node), target_mesh, 1.0))
    new_aliases = cmds.aliasAttr(blendshape_node, q=True) 
    #compare the old aliases with the current aliases
    for i in range(0,len(new_aliases),2):
        if new_aliases[i] not in old_aliases:
            new_alias_attr = new_aliases[i]
            break
    cmds.aliasAttr(name, '{blendshape_node}.{new_alias_attr}'.format(**locals()))
def get_number_of_blendshape_targets(blendshape_node):
    """Returns the number of blendshape targets in a blendshape node."""
    alias_list = cmds.aliasAttr(blendshape_node, q=True)
    if alias_list:
        return len(alias_list) // 2
    else:
        return 0
def duplicate_shapes(blendshape_node,targets,base_mesh):
    shapes_and_weights = []
    for target in targets:
        weights,_,_,_ = find_inbetween_weights_from_target_name(blendshape_node, target)
        shapes = []
        for weight in weights:
            cmds.setAttr(blendshape_node + '.' + target, weight)
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
def create_inbetweener_driver(a,b,c,driver_input,second_first = False, second_last = False):
    """Create a node network that looks like __ a/b\c __. Returns the output attribute of the node network."""
    #Creates a system of nodes that computes f(x,a,b,c) = max(1 + min ((b-x)/(c-b), (b-x)/(a-b)), 0)
    #first create the float math nodes 
    bMinusX = cmds.shadingNode('floatMath', asUtility=True, name='bMinusX#')
    cmds.setAttr(bMinusX + ".isHistoricallyInteresting", 0)
    cmds.setAttr(bMinusX + '.operation', 1) #subtract
    cmds.setAttr(bMinusX + '.floatA', b)
    cmds.connectAttr(driver_input, bMinusX + '.floatB')

    aMinusB = cmds.shadingNode('floatMath', asUtility=True, name='aMinusB#')
    cmds.setAttr(aMinusB + ".isHistoricallyInteresting", 0)
    cmds.setAttr(aMinusB + '.operation', 1) #subtract
    cmds.setAttr(aMinusB + '.floatA', a)
    cmds.setAttr(aMinusB + '.floatB', b)

    cMinusB = cmds.shadingNode('floatMath', asUtility=True, name='cMinusB#')
    cmds.setAttr(cMinusB + ".isHistoricallyInteresting", 0)
    cmds.setAttr(cMinusB + '.operation', 1) #subtract
    cmds.setAttr(cMinusB + '.floatA', c)
    cmds.setAttr(cMinusB + '.floatB', b)

    ratioC = cmds.shadingNode('floatMath', asUtility=True, name='ratioC#')
    cmds.setAttr(ratioC + ".isHistoricallyInteresting", 0)
    cmds.setAttr(ratioC + '.operation', 3) #divide
    cmds.connectAttr(bMinusX + '.outFloat', ratioC + '.floatA')
    cmds.connectAttr(cMinusB + '.outFloat', ratioC + '.floatB')

    ratioA = cmds.shadingNode('floatMath', asUtility=True, name='ratioA#')
    cmds.setAttr(ratioA + ".isHistoricallyInteresting", 0)
    cmds.setAttr(ratioA + '.operation', 3) #divide
    cmds.connectAttr(bMinusX + '.outFloat', ratioA + '.floatA')
    cmds.connectAttr(aMinusB + '.outFloat', ratioA + '.floatB')

    minRatio = cmds.shadingNode('floatMath', asUtility=True, name='minRatio#')
    cmds.setAttr(minRatio + ".isHistoricallyInteresting", 0)
    cmds.setAttr(minRatio + '.operation', 4) #minimum
    cmds.connectAttr(ratioA + '.outFloat', minRatio + '.floatA')
    cmds.connectAttr(ratioC + '.outFloat', minRatio + '.floatB')

    #add one
    addOne = cmds.shadingNode('floatMath', asUtility=True, name='addOne#')
    cmds.setAttr(addOne + ".isHistoricallyInteresting", 0)
    cmds.setAttr(addOne + '.operation', 0) #add
    cmds.setAttr(addOne + '.floatA', 1)
    cmds.connectAttr(minRatio + '.outFloat', addOne + '.floatB')

    #clam value to positive with max
    clampNegative = cmds.shadingNode('floatMath', asUtility=True, name='clampNegative#')
    cmds.setAttr(clampNegative + ".isHistoricallyInteresting", 0)
    cmds.setAttr(clampNegative + '.operation', 5) #maximum
    cmds.setAttr(clampNegative + '.floatA', 0)
    cmds.connectAttr(addOne + '.outFloat', clampNegative + '.floatB')

    #If second first we need to plug min(0,ratioC) clambNegative.floatA
    if second_first and second_last:
        #Effectively ignores the max clamp
        cmds.connectAttr(addOne + '.outFloat', clampNegative + '.floatA')
    elif second_first:
        minZeroC = cmds.shadingNode('floatMath', asUtility=True, name='minZeroC#')
        cmds.setAttr(minZeroC + ".isHistoricallyInteresting", 0)
        cmds.setAttr(minZeroC + '.operation', 4)
        cmds.connectAttr(ratioA + '.outFloat', minZeroC + '.floatA')
        cmds.setAttr(minZeroC + '.floatB', 0)
        cmds.connectAttr(minZeroC + '.outFloat', clampNegative + '.floatA')
    elif second_last:
        minZeroA = cmds.shadingNode('floatMath', asUtility=True, name='minZeroA#')
        cmds.setAttr(minZeroA + ".isHistoricallyInteresting", 0)
        cmds.setAttr(minZeroA + '.operation', 4)
        cmds.connectAttr(ratioC + '.outFloat', minZeroA + '.floatA')
        cmds.setAttr(minZeroA + '.floatB', 0)
        cmds.connectAttr(minZeroA + '.outFloat', clampNegative + '.floatA')
    return clampNegative + '.outFloat'

    #But if it's not an ibetween shape we 

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
    
def rename_blendshape_target(blendshape_node, old_alias, new_alias):
    '''
    rename_blendshape_target('C_baseShape_BLS', 'C_eyebrowUp_PLY', 'C_eyebrowDown_PLY')
    '''
    all_aliases = cmds.aliasAttr(blendshape_node, q=True) 
    # format: ['alias0', 'weight[0]', 'alias1', 'weight[1]']
    if not old_alias in all_aliases:
        raise ValueError(
            "BlendShape node '{blendshape_node}' doesn't have an alias '{old_alias}'".format(**locals()))
    old_alias_attr_index = all_aliases.index(old_alias) + 1
    old_alias_attr = all_aliases[old_alias_attr_index]
    cmds.aliasAttr(new_alias, '{blendshape_node}.{old_alias_attr}'.format(**locals()))
def get_blendshape_nodes():
    """
    Returns a list of blendshape nodes in the scene.
    """
    return cmds.ls(type='blendShape')
def bake_blendnode(*args):
    """
    Callback function for the generate button.
    """
    blendshape_node = cmds.optionMenu("blendshapeNodeMenu", query=True, value=True)
    delete_orignal_node = cmds.checkBox("DeleteOriginalNode", query=True, value=True)
    make_unreal_compatible = cmds.checkBox("UnrealCompatibleInbetweens", query=True, value=True)
    bake_blendshape_painted_weights(blendshape_node, make_unreal_compatible, delete_orignal_node)
def create_ui():
    """
    UI for baker.
    """
    window_id = 'blendshake_baker_UI'
    
    if cmds.window(window_id, exists=True):
        cmds.deleteUI(window_id)
    
    cmds.window(window_id, title="Blendnode Baker", widthHeight=(200, 150))
    cmds.columnLayout(adjustableColumn=True)
    cmds.text(label="Select Blendshape Node:")

    
    # Blendshape node menu
    cmds.optionMenu("blendshapeNodeMenu")
    for node in get_blendshape_nodes():
        cmds.menuItem(label=node)

    #Add button for Unreal Engine compatibility
    cmds.checkBox("UnrealCompatibleInbetweens",label="Unreal Compatible Inbetweens", value=True)
    #add button "delete original node"
    cmds.checkBox("DeleteOriginalNode",label="Delete Original Node", value=True)
    
    
    # Generate button
    cmds.button(label="Bake to UE4 compatible", command=bake_blendnode)
    
    cmds.showWindow()

if __name__ == '__main__':
    create_ui()
