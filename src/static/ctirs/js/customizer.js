$(function() {

  const NODE_TYPE_OBJECT = 'eclipse'
  const NODE_TYPE_PROPERTY_STRING = 'box'
  const NODE_DEFAULT_COLOR = '#D2E5FF'
  const EDGE_DEFAULT_COLOR = {
      opacity: 1.0,
      color: '#777777'
    }

  const EDGE_TYPE_CONTAINS = 'contains'
  const EDGE_TYPE_MATCHES = 'matches'
  const EDGE_TYPE_CONSISTS_OF = 'consists-of'

  const DATA_TYPE_OBJECT = 'object'
  const DATA_TYPE_PROPERTY = 'property'

  const VAL_TYPE_STRING = 'string'
  const VAL_TYPE_DICT = 'dict'

  const OPERATION_TYPE_ADD_NODE = 'add_node'
  const OPERATION_TYPE_EDIT_NODE = 'edit_node'
  const OPERATION_TYPE_ADD_EDGE = 'add_edge'
  const OPERATION_TYPE_EDIT_EDGE = 'edit_edge'

  var network = null
  var matching_names = {}
  var custom_property_dict = {}


  function destroy() {
    if (network !== null) {
      network.destroy()
      network = null
      matching_names = {}
      custom_property_dict = {}
    }
  }

  function _update_graph_matching(matching_patterns, nodes, edges) {
    $.each(matching_patterns,function(key_obj,mp) {
      const targets = mp.targets
      $.each(targets, function(key_source,source) {
        $.each(targets, function(key_target, target) {
          if (key_source < key_target) {
            const source_node = custom_property_dict[source]
            const target_node = custom_property_dict[target]
            if ((source_node != undefined) && (target_node != undefined)) {
              const edge = _get_matches_edge(source_node.id, target_node.id, mp.name)
              edges.add(edge)
              matching_names[edge.id] = mp.name
            }
          }
        })
      })
    })
  }

  function _update_graph_custom_objects(custom_objects, nodes, edges) {
    $.each(custom_objects, function(key_obj, co) {
      var co_node = _get_node_from_custom_object(co)
      nodes.add(co_node)
      const dict_list = {}
      $.each(co.properties, function(key_prop, cp) {
        const split_name = cp.name.split('.')
        var dict_key = null
        var prop_node = null
        if (split_name.length == 1) {
          const cp_node = _get_node_from_custom_property(cp, co_node, cp.name, false)
          nodes.add(cp_node)
          const edge = _get_contains_edge(co_node.id, cp_node.id)
          edges.add(edge)
          prop_node = cp_node
        } else {
          const dict_name = split_name[0]
          const object_name = co_node.label

          if (object_name in dict_list == false){
            dict_list[object_name] = {}
          }
          var dict_node = null
          if (dict_name in dict_list[object_name] == false) {
            dict_node = _get_node_from_custom_property(cp, co_node, split_name[0], true)
            nodes.add(dict_node)
            const contains_edge = _get_contains_edge(co_node.id, dict_node.id)
            edges.add(contains_edge)
            dict_node_id = dict_node.id
            dict_list[object_name] = {}
            dict_list[object_name] [dict_name] = dict_node
          }else {
            dict_node = dict_list[object_name][dict_name]
          }

          const child_node = _get_node_from_custom_property(cp, co_node, split_name[1], false)
          child_node.dict_name = split_name[0]
          child_node.dict_id = dict_node_id

          if ('child_nodes' in nodes._data[dict_node_id] == false) {
            nodes._data[dict_node_id].child_nodes = []
          }
          nodes._data[dict_node_id].child_nodes.push(child_node)
          nodes.add(child_node)

          const consists_of_edge = _get_consists_of_edge(dict_node.id, child_node.id)
          edges.add(consists_of_edge)
          prop_node = child_node
        }
        dict_key = co.name + ':' + cp.name
        custom_property_dict[dict_key] = prop_node
      })
    })
  }

  function updateGraph(dataSource) {
    if (dataSource == null) {
      return
    }
    var nodes = new vis.DataSet([])
    var edges = new vis.DataSet([])

    _update_graph_custom_objects(dataSource.custom_objects, nodes, edges)
    _update_graph_matching(dataSource.matching_patterns, nodes, edges)
    _start_network(nodes, edges, null)
  }

  function _get_node_from_custom_object(co) {
    var d = {
      type:  DATA_TYPE_OBJECT,
      parent: null,
      label: co.name,
      color: co.color,
      shape: NODE_TYPE_OBJECT,
      borderWidth: 1,
      shapeProperties: { borderDashes: [10, 10] },
    }
    return d
  }

  function _init_property_node() {
    var required = false
    var val_type = VAL_TYPE_STRING
    var regexp = null

    var fuzzy_matching = {
      case_insensitive: false,
      match_kata_hira: false,
      match_zen_han: false,
      match_eng_jpn: false,
      list_matching: false,
      lists: [],
    }

    var prop = {
      type:  DATA_TYPE_PROPERTY,
      parent: null,
      label: '',
      color: '',
      required: required,
      val_type: val_type,
      regexp: regexp,
      fuzzy_matching: fuzzy_matching,
      shape: NODE_TYPE_PROPERTY_STRING,
      borderWidth: 1,
      shapeProperties: { borderDashes: [10, 10] },
    }
    return prop
  }

  function _get_node_from_custom_property(cp, co_node, label, is_dict) {
    var node = _init_property_node()
    if ('required' in cp) {
      node.required = cp['required']
    }
    if ('regexp' in cp) {
      node.regexp = cp['regexp']
    }
    if ('fuzzy_matching' in cp) {
      node.fuzzy_matching = cp['fuzzy_matching']
    }

    if(is_dict){
      node.val_type = VAL_TYPE_DICT
    }else {
      if ('type' in cp) {
        node.val_type = cp['type']
      }
   }
    node.parent = co_node.label
    node.label = label
    node.color = co_node.color
    return node
  }

  function _get_consists_of_edge(dict_id, child_id) {
    var d = {
      from: dict_id,
      to: child_id,
      type: EDGE_TYPE_CONSISTS_OF
    }
    d.label = EDGE_TYPE_CONSISTS_OF
    d.color = EDGE_DEFAULT_COLOR
    d.smooth = false
    d.chosen = false
    return d
  }

  function _get_contains_edge(obj_id, prop_id) {
    var d = {
      from: obj_id,
      to: prop_id,
      type: EDGE_TYPE_CONTAINS
    }
    d.label = EDGE_TYPE_CONTAINS
    d.color = EDGE_DEFAULT_COLOR
    d.smooth = false
    d.chosen = false
    return d
  }

  function _get_matches_edge(obj_id, prop_id, matching_name) {
    var d = {
      from: obj_id,
      to: prop_id,
      matching_name: matching_name,
      label: EDGE_TYPE_MATCHES,
      type: EDGE_TYPE_MATCHES
    }
    d.color = {
      opacity: 1.0,
      color: '#777777'
    }
    d.smooth = false
    d.chosen = false
    return d
  }

  function _start_network(nodes, edges, config_dom) {
    var container = document.getElementById('visjs-network')
    var data = {
      nodes: nodes,
      edges: edges
    }

    var default_options = {
      autoResize: false,
      physics: {
        enabled: false,
        stabilization: {
          enabled: true
        }
      },
      manipulation: {
        addNode: function(data, callback) {
          addNode(data, callback)
        },
        editNode: function(data, callback) {
          editNode(data, callback)
        },
        deleteNode: function(data, callback) {
          deleteNode(data, callback)
        },
        addEdge: function(data, callback) {
          if (data.from == data.to) {
            alert('Can not connect the node to itself.')
            return
          }
          editEdgeWithoutDrag(OPERATION_TYPE_ADD_EDGE, data, callback)

        },
        editEdge: {
          editWithoutDrag: function(data, callback) {
            document.getElementById('edge-operation').innerText =
              'Edit Edge'
            editEdgeWithoutDrag(OPERATION_TYPE_EDIT_EDGE, data, callback)
          },
        },
        deleteEdge: function(data, callback) {
          deleteEdge(data, callback)
        },
      }
    }
    var options = default_options
    destroy()
    network = new vis.Network(container, data, options)
  }

  function addNode(data, callback) {
    $('#add-node-name').val('')
    document.getElementById('add-node-saveButton').onclick = saveNodeData.bind(
      this,
      OPERATION_TYPE_ADD_NODE,
      data,
      callback
    )
    document.getElementById('add-node-cancelButton').onclick =
      clearNodePopUp.bind(this, OPERATION_TYPE_ADD_NODE, callback)

    $('#add-prefix-span').html('x-&nbsp;')
    $('#add-type-object').prop('checked', true)
    $('#add-node-popUp').css({'display': 'block'})
  }

  function deleteNode(data, callback) {
    $.each(data.nodes, function(_, node_id) {
      const node = getNode(node_id)
      const node_type = node.options.type
      if (node_type == 'property'){
        if(node.options.val_type != VAL_TYPE_DICT) {
          if ('dict_id' in node.options) {
            if (node.options.dict_id in network.body.nodes) {
              const dict_node = network.body.nodes[node.options.dict_id]
              delete(dict_node.options.child_nodes[node.id])
              if(Object.keys(dict_node.options.child_nodes).length == 0) {
                network.body.nodes[node.options.dict_id].options.val_type = VAL_TYPE_STRING
              }
            }
          }
          if (node.options.dict_id in network.body.nodes) {
            const temp_child_nodes = []
            $.each(network.body.nodes[node.options.dict_id].options.child_nodes, function (_, child_node) {
              if (child_node.dict_id != node.options.dict_id) {
                temp_child_nodes.push(child_node)
              }
            })
            network.body.nodes[node.options.dict_id].options.child_nodes = temp_child_nodes
          }
          $.each(node.edges, function(_, delete_edge) {
            if (delete_edge.options.label == EDGE_TYPE_MATCHES) {
              delete(matching_names[delete_edge.id])
            }
          })
        } else {
          $.each(node.options.child_nodes, function(_, child_node) {
            delete(network.body.nodes[child_node.id].options.parent)
            delete(network.body.nodes[child_node.id].options.dict_name)
          })
        }

        callback(data)
      } else{
        if(data.edges.length > 0){
          alert('Can not delete the object node which has edge (s)')
          data.nodes = []
          data.edges = []
        }
        callback(data)
      }
    })
    return
  }

  function deleteEdge(data, callback) {
    $.each(data.edges, function(key, edge_id){
      const edge = network.body.edges[edge_id].options
      if (edge.label == EDGE_TYPE_MATCHES) {
        _delete_match_edge(edge_id)
      }
    })
    callback(data)
    return
  }

  function _delete_match_edge(edge_id) {
    const edge = network.body.edges[edge_id].options
    if (edge_id in matching_names) {
      delete(matching_names[edge_id])
    }
    $.each(network.getConnectedNodes(edge_id), function(key2, node_id){
      if(network.body.nodes[node_id].options.val_type == VAL_TYPE_DICT) {
        network.body.nodes[node_id].options.val_type = VAL_TYPE_STRING
      }
    })
  }

  function editNode(data, callback) {
    $('#edit-node-name').val(data.label)

    var title = ''
    if (data.type == DATA_TYPE_PROPERTY) {
      title = 'Edit Custom Property'
      $('#edit-type-property').prop('checked', true)
      $('#edit-node-object-div').css({'display': 'none'})
      $('#edit-node-property-div').css({'display': 'block'})
      $('#edit-common-regexp').val(data.regexp)
      $('#edit-common-val-type').val(data.val_type)
      $('#edit-common-required').prop('checked', data.required)
      $('#edit-fuzzy-case-insensitive').prop('checked', data.fuzzy_matching.case_insensitive)
      $('#edit-fuzzy-kata-hira').prop('checked', data.fuzzy_matching.match_kata_hira)
      $('#edit-fuzzy-zen-han').prop('checked', data.fuzzy_matching.match_zen_han)
      $('#edit-fuzzy-eng-jpn').prop('checked', data.fuzzy_matching.match_eng_jpn)
      $('#edit-fuzzy-list').prop('checked', data.fuzzy_matching.list_matching)
      if (data.fuzzy_matching.list_matching != true) {
        $('.edit-fuzzy-list-textarea').prop('disabled', true)
      }
      if (data.fuzzy_matching.lists.length != 0) {
        $('#edit-fuzzy-list-init').css({'display': 'none'})
      }
      var list_div = $('#edit-fuzzy-list-div')
      list_div.empty()
      $.each(data.fuzzy_matching.lists, function(key, fuzzy_matching_list) {
        var list_contents = ''
        $.each(fuzzy_matching_list, function(key2, content) {
          list_contents += content
          list_contents += '\n'
        })
        var textarea = $('<textarea>', {
          'class': 'form-control edit-fuzzy-list-textarea',
          'rows': 3
        })
        textarea.val(list_contents)
        list_div.append(textarea)
      })
    } else {
      title = 'Edit Custom Object'
      $('#edit-type-object').prop('checked', true)
      $('#edit-common-color').val(data.color.background)
      $('#edit-node-object-div').css({'display': 'block'})
      $('#edit-node-property-div').css({'display': 'none'})
    }
    $('#edit-node-operation').text(title)

    document.getElementById('edit-node-saveButton').onclick = saveNodeData.bind(
      this,
      OPERATION_TYPE_EDIT_NODE,
      data,
      callback
    )
    document.getElementById('edit-node-cancelButton').onclick =
      cancelNodeEdit.bind(this, callback)
    if (network.body.nodes[data.id].options.val_type == VAL_TYPE_DICT){
      $('#edit-common-regexp').prop('disabled', true)
      $('#edit-common-required').prop('disabled', true)
      $('#edit-fuzzy-case-insensitive').prop('disabled', true)
      $('#edit-fuzzy-kata-hira').prop('disabled', true)
      $('#edit-fuzzy-zen-han').prop('disabled', true)
      $('#edit-fuzzy-eng-jpn').prop('disabled', true)
      $('#edit-fuzzy-list').prop('disabled', true)
      $('.edit-fuzzy-list-textarea').prop('disabled', true)
      $('#edit-fully-list-plus').css({'display': 'none'})
    }
    $('#edit-node-popUp').css({'display': 'block'})
  }

  function clearNodePopUp(operation_type) {
    if (operation_type == OPERATION_TYPE_ADD_NODE) {
      document.getElementById('add-node-saveButton').onclick = null
      document.getElementById('add-node-cancelButton').onclick = null
      $('#add-node-popUp').css({'display': 'none'})
    } else {
      document.getElementById('edit-node-saveButton').onclick = null
      document.getElementById('edit-node-cancelButton').onclick = null
      $('#edit-node-popUp').css({'display': 'none'})
    }
  }

  function cancelNodeEdit(callback) {
    clearNodePopUp(OPERATION_TYPE_EDIT_NODE)
    callback(null)
  }

  function getNodeBase(operation_type) {
    if (operation_type == OPERATION_TYPE_ADD_NODE) {
      return $('#add-node-name').val()
    } else {
      return $('#edit-node-name').val()
    }
  }

  function getNodeType(operation_type) {
    var selector = null
    if (operation_type == OPERATION_TYPE_ADD_NODE) {
      selector = $('#add-type-object')
    } else {
      selector = $('#edit-type-object')
    }
    if (selector.prop('checked') == true) {
      return DATA_TYPE_OBJECT
    } else {
      return DATA_TYPE_PROPERTY
    }
  }

  function saveNodeData(operation_type, data, callback) {
    var node_base = getNodeBase(operation_type)
    var node_type = getNodeType(operation_type)
    var before_label = ''

    if (node_base.length == 0) {
      alert('Fill the Object or Property Name')
      return
    }
    if ((node_base.startsWith('x-') == true) || (node_base.startsWith('x_') == true)) {
      node_base = node_base.substring(2)
    }

    if (node_type == DATA_TYPE_OBJECT) {
      before_label = data.label
      data.shape = NODE_TYPE_OBJECT
      data.label = 'x-' + node_base
      data.type = DATA_TYPE_OBJECT
    } else if (node_type == DATA_TYPE_PROPERTY) {
      data.shape = NODE_TYPE_PROPERTY_STRING
      data.label = 'x_' + node_base
      data.type = DATA_TYPE_PROPERTY
    } else {
      alert('Wrong type value')
      return
    }

    if (operation_type == OPERATION_TYPE_ADD_NODE) {
      if (isExistObjectNode(data) == true) {
        alert('The Same Property or Object Node has already existed.')
        return
      }

      data.color = NODE_DEFAULT_COLOR
      data.shapeProperties = { borderDashes: [10, 10] }
      if (node_type == DATA_TYPE_PROPERTY) {
        var init_property_node = _init_property_node()
        data.required = init_property_node.required
        data.val_type = init_property_node.val_type
        data.regexp = init_property_node.regexp
        data.fuzzy_matching = init_property_node.fuzzy_matching
      }
    } else {
      if (node_type == DATA_TYPE_OBJECT) {
        data.color = $('#edit-common-color').val()
        inheritProperty(before_label, data.label, data.color)
      } else {
        data.required = $('#edit-common-required').prop('checked')
        data.regexp = $('#edit-common-regexp').val()
        var fuzzy_matching = {}
        fuzzy_matching.case_insensitive = $('#edit-fuzzy-case-insensitive').prop('checked')
        fuzzy_matching.match_kata_hira= $('#edit-fuzzy-kata-hira').prop('checked')
        fuzzy_matching.match_zen_han= $('#edit-fuzzy-zen-han').prop('checked')
        fuzzy_matching.match_eng_jpn= $('#edit-fuzzy-eng-jpn').prop('checked')
        fuzzy_matching.list_matching= $('#edit-fuzzy-list').prop('checked')
        var lists = []
        $.each($('.edit-fuzzy-list-textarea'), function(key, ta) {
          var fuzzy_list = []
          var content = ta.value
          if (content.length == 0) {
            return true
          }
          var lines = content.split('\n')
          $.each(lines, function(key2, line) {
            if (line.length == 0) {
              return true
            }
            fuzzy_list.push(line)
          })
          lists.push(fuzzy_list)
        })
        fuzzy_matching.lists = lists
        data.fuzzy_matching = fuzzy_matching
      }
    }
    clearNodePopUp(operation_type)
    callback(data)
  }

  function inheritProperty(before_label, after_label, after_color) {
    $.each(network.body.nodes, function(key, index) {
      var node = network.body.nodes[key].options
      if (node.type == DATA_TYPE_PROPERTY) {
        if (node.parent == before_label) {
          network.body.nodes[key].options.parent = after_label
          network.body.nodes[key].options.color.background = after_color
        }
      }
    })
  }

  function getNode(node_id) {
    var id_ = null
    if (typeof(node_id) == 'string') {
      id_ = node_id
    } else {
      id_ = node_id.id
    }
    return network.body.nodes[id_]
  }

  function isExistObjectNode(node) {
    var ret = false
    $.each(network.body.nodes, function(key, network_node) {
      var options = network_node.options
      if (node.type == DATA_TYPE_OBJECT) {
        if ((options.type == DATA_TYPE_OBJECT) && (options.label == node.label)) {
          ret = true
          return false
        }
      } else {
        if ((options.type == DATA_TYPE_PROPERTY) && (options.parent == null) && (options.label == node.label)) {
          ret = true
          return false
        }
      }
    })
    return ret
  }

  function editEdgeWithoutDrag(operation_type, data, callback) {
    var from = getNode(data.from)
    var to = getNode(data.to)

    data.type = null
    var prop_color = null
    if (from.options.type == DATA_TYPE_OBJECT) {
      if (to.options.type == DATA_TYPE_OBJECT) {
        alert('Cannot create an edge between "OBJECT" type nodes')
        return
      } else {
        data.type = EDGE_TYPE_CONTAINS
        prop_color = from.options.color
      }
    } else {
      if (to.options.type == DATA_TYPE_OBJECT) {
        data.type = EDGE_TYPE_CONTAINS
        prop_color = to.options.color
      } else {
        data.type = EDGE_TYPE_MATCHES
      }
    }

    var dict_node = null
    var child_node = null
    if (data.type == EDGE_TYPE_MATCHES) {
      if ((from.options.parent == undefined) && (to.options.parent != undefined)){
        dict_node = to
        child_node = from
      }
      else if ((from.options.parent != undefined) && (to.options.parent == undefined)) {
        dict_node = from
        child_node = to
      }
      if (dict_node){
        data.type = EDGE_TYPE_CONSISTS_OF
      }
    }

    if (data.type == EDGE_TYPE_CONTAINS) {
      _set_contains_edge_dialog(operation_type, prop_color, data, from, to, callback)
    } else if (data.type == EDGE_TYPE_MATCHES) {
      _set_matching_edge_dialog(operation_type, data, from, to, callback)
    } else {
     _set_consists_of_edge(operation_type, data, dict_node, child_node, callback)
    }
  }

  function _set_contains_edge_dialog(operation_type, prop_color, data, from, to, callback) {
    if (operation_type == OPERATION_TYPE_EDIT_EDGE) {
      alert('Cannot edit a contains edge')
      callback(null)
      return
    }

    var prop_id = null
    var prop_name = null
    var object_node = null
    if (from.options.type == DATA_TYPE_PROPERTY) {
      prop_id = data.from
      prop_name = from.options.label
      object_node = to
      prop_node = from
    } else {
      prop_id = data.to
      prop_name = to.options.label
      object_node = from
      prop_node = to
    }
    if (network.getConnectedNodes(prop_id).length != 0) {
      alert('Cannot connect nodes which has already an edge')
      return
    }

    $.each(network.getConnectedNodes(prop_id), function (k, connected_node_id){
      const connected_node = network.body.nodes[connected_node_id]
      alert('Cannot connect nodes which has already an edge')
      return
    })

    if (_is_duplicate_property(object_node, prop_name) == true) {
      alert('This object has already the same property')
      return
    }
    data.label = EDGE_TYPE_CONTAINS
    prop_node.options.color = prop_color
    _save_contains_edge(data, callback)
  }

  function _set_matching_edge_dialog(operation_type, data, from, to, callback) {
    if ((from.options.parent == undefined) && (to.options.parent == undefined)) {
      alert('Cannot connect property nodes which do not define a parent object')
      callback(null)
      return
    }
    if (from.options.parent == to.options.parent) {
      alert('Cannot connect property nodes that belongs to the same object')
      callback(null)
      return
    }
    if (operation_type == OPERATION_TYPE_ADD_EDGE) {
      if (network.getConnectedNodes(from.id).includes(to.id)){
        alert('Cannot connect property nodes which has been alredy connected with a matched link')
        callback(null)
        return
      }
    }
    if ((from.options.val_type != VAL_TYPE_STRING) || (to.options.val_type != VAL_TYPE_STRING)) {
        alert('Cannnot connect nodes whose type are dictionary.')
        callback(null)
        return
    }

    data.from = from.id
    data.to = to.id

    var matching_name = null
    if (operation_type == OPERATION_TYPE_EDIT_EDGE) {
      matching_name = matching_names[data.id]
    } else {
      matching_name = ''
    }
    $('#edit-edge-rule-name').val(matching_name)
    document.getElementById('edge-saveButton').onclick = _save_matching_edge.bind(
      this,
      data,
      callback
    )
    document.getElementById('edge-cancelButton').onclick = cancelEdgeEdit.bind(this, callback)
    document.getElementById('edge-operation').innerText = 'Connect a matching link.'
    document.getElementById('edge-div-rule-name').style.display = 'block'
    document.getElementById('edge-popUp').style.display = 'block'
  }

  function _set_consists_of_edge(operation_type, data, dict_node, child_node, callback) {
    if (operation_type == OPERATION_TYPE_EDIT_EDGE) {
      alert('Cannot edit consists-of edge')
      callback(null)
      return
    }
    _save_consists_of_edge(data, dict_node, child_node, callback)
  }

  function _is_duplicate_property(object_node, prop_name) {
    var ret = false
    $.each(object_node.edges, function(key_edge, edge) {
      var tmp_prop = null
      if(edge.fromId == object_node.id){
        tmp_prop = getNode(edge.toId)
      } else {
        tmp_prop = getNode(edge.fromId)
      }
      if (tmp_prop.options.label == prop_name) {
        ret = true
        return true
      }
    })
    return ret
  }

  function clearEdgePopUp() {
    document.getElementById('edge-saveButton').onclick = null
    document.getElementById('edge-cancelButton').onclick = null
    document.getElementById('edge-popUp').style.display = 'none'
  }

  function cancelEdgeEdit(callback) {
    clearEdgePopUp()
    callback(null)
  }

  function _save_consists_of_edge(data, dict_node, child_node, callback) {
    const child_label = child_node.options.label
    if ('child_nodes' in  network.body.nodes[dict_node.id].options) {
      const child_nodes = Object.values(network.body.nodes[dict_node.id].options.child_nodes)
      if (child_nodes.includes(child_label)) {
        alert('This property has been added')
        clearEdgePopUp()
        return
      }
    } else {
      network.body.nodes[dict_node.id].options.child_nodes = {}
    }
    network.body.nodes[dict_node.id].options.child_nodes[child_node.id] = child_label

    network.body.nodes[child_node.id].options.parent = network.body.nodes[dict_node.id].options.parent
    network.body.nodes[dict_node.id].options.val_type = VAL_TYPE_DICT
    network.body.nodes[child_node.id].options.val_type = VAL_TYPE_STRING
    network.body.nodes[child_node.id].options.dict_name = dict_node.options.label
    network.body.nodes[child_node.id].options.dict_id = dict_node.id
    network.body.nodes[child_node.id].options.color = network.body.nodes[dict_node.id].options.color
    data.label = data.type
    data.smooth = false
    data.chosen = false
    clearEdgePopUp()
    callback(data)
  }

  function _save_contains_edge(data, callback) {
    data.label = data.type
    data.smooth = false
    data.chosen = false
    network.body.nodes[data.to].options.parent = network.body.nodes[data.from].options.label
    clearEdgePopUp()
    callback(data)
  }

  function _save_matching_edge(data, callback) {
    const rule_name = $('#edit-edge-rule-name').val()
    if (Object.values(matching_names).includes(rule_name)){
      alert('This rule name has already existed.')
      return
    }
    data.label = data.type
    data.smooth = false
    data.chosen = false
    clearEdgePopUp()
    callback(data)
    matching_names[data.id] = rule_name
  }

  $('#edit-fuzzy-list').on('change', function() {
    $('.edit-fuzzy-list-textarea').prop('disabled', !$(this).prop('checked'))
  })

  $('.add-type-radio').on('change', function() {
    if ($('#add-type-object').prop('checked') == true) {
      $('#add-prefix-span').html('x-&nbsp;&nbsp;')
    }
    if ($('#add-type-property').prop('checked') == true) {
      $('#add-prefix-span').html('x_&nbsp;&nbsp;')
    }
  })

  $('#edit-fully-list-plus').on('click', function() {
    var list_div = $('#edit-fuzzy-list-div')
    var textarea = $('<textarea>', {
      'class': 'form-control edit-fuzzy-list-textarea',
      'rows': 3
    })
    list_div.append(textarea)
  })

  $('#discard-button').on('click', function() {
    ret = confirm('Would you like to discard the configuration?')
    if (ret == true) {
      network.destroy()
      init_draw()
    }
  })

  function _get_custom_objects_json () {
    var work_custom_objects = {}
    $.each(network.body.nodes, function(key, network_node) {
      var node = network_node.options
      if (node.type == DATA_TYPE_OBJECT) {
        var co = {}
        co.name = node.label
        co.color = node.color.background
        co.properties = []
        work_custom_objects[co.name] = co
      }
    })

    var msg = null
    $.each(network.body.nodes, function(key, network_node) {
      var node = network_node.options
      if (node.type == DATA_TYPE_PROPERTY) {
        if (node.parent in work_custom_objects == false) {
          msg = 'Property: ' + node.label + ' does not belong to any object.'
          return false
        }
        const co = work_custom_objects[node.parent]
        if ('parent' in node == false) {
          return true
        }
        if (node.val_type == VAL_TYPE_STRING) {
          co.properties.push(_get_property_from_node(node))
        }
      }
    })
    if (msg) {
      alert(msg)
      return null
    }

    function _get_property_from_node (node) {
      const prop = {}
      if ('dict_name' in node) {
        prop.name = node.dict_name + '.' + node.label
      } else{
        prop.name = node.label
      }
      prop.required = node.required
      prop.type = node.val_type
      prop.regexp = node.regexp
      if (prop.regexp != null) {
        if (prop.regexp.length == 0) {
          prop.regexp = null
        }
      }
      prop.fuzzy_matching = node.fuzzy_matching
      return prop
    }

    var custom_objects = []
    $.each(work_custom_objects, function(key, co) {
      if (co.properties.length == 0) {
        return true
      }
      custom_objects.push(co)
    })
    return custom_objects
  }

  function _get_matching_patterns_json () {
    var work_matching_patterns =  {}
    $.each(network.body.edges, function(key, edge) {
      var options = edge.options
      function _get_target_from_node(node) {
        var target = {}
        target.object = node.options.parent
        if ('dict_name' in node.options) {
          target.property = node.options.dict_name + '.' + node.options.label
        } else {
          target.property = node.options.label
        }
        return target
      }

      function _has_target(targets, target){
        var flag = false
        $.each(targets, function(key, elem) {
          if ((target.object == elem.object) && (target.property == elem.property)) {
            flag = true
            return true
          }
        })
        return flag
      }

      function _add_target(matching_name, target) {
        var targets = null
        if (matching_name in work_matching_patterns == true) {
          targets = work_matching_patterns[matching_name]
        } else {
          targets = []
        }
        if (_has_target(targets, target) == false) {
          targets.push(target)
        }
        work_matching_patterns[matching_name] = targets
        return
      }

      if (options.label == EDGE_TYPE_MATCHES) {
        var matching_name = matching_names[edge.id]
        var node = null
        node = _get_target_from_node(edge.from)
        _add_target(matching_name, node)
        node = _get_target_from_node(edge.to)
        _add_target(matching_name, node)
      }
    })

    var matching_patterns = []
    $.each(work_matching_patterns, function(name, targets) {
      matching_patterns.push({
        name: name,
        type: 'Exact',
        targets: targets
      })
    })
    return matching_patterns
  }

  $('#save-button').on('click', function() {
    var ret = {}
    ret.custom_objects =  _get_custom_objects_json()
    if (ret.custom_objects == null){
      return
    }
    ret.matching_patterns = _get_matching_patterns_json()

    $.ajax({
      url: '/configuration/customizer/set_configuration/',
      data:JSON.stringify(ret),
      contentType: 'application/json',
      dataType: 'json',
      type: 'post',
      cache: false,
      async: false,
    })
    .done(function(data, textStatus, jqXHR) {
      alert('Custom Objects are successfully saved')
    })
    .fail(function(jqXHR, textStatus, errorThrown) {
      if (jqXHR.status == 201) {
        alert('Custom Objects are successfully saved')
      } else {
        alert(jqXHR.statusText)
      }
    })
  })

  function init_draw() {
    $.ajax({
      url: '/configuration/customizer/get_configuration/',
      data: {},
      type: 'get',
      cache: false,
      async: false,
    })
    .done(function(data, textStatus, jqXHR) {
      updateGraph(data)
    })
    .fail(function(jqXHR, textStatus, errorThrown) {
      alert(jqXHR.statusText)
    })
  }

  $(window).on('load', function() {
    init_draw()
  })
})
