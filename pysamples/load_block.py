#Copyright (c) 2011, Walter Bender

# This procedure is invoked when the user-definable block on the
# "extras" palette is selected.

# Usage: Import this code into a Python (user-definable) block; when
# this code is run, the turtle will create a block at the current
# location of the turtle.  The first argument to the Python block
# should be a string containing the name of the desired
# block. Arguments to the block can be passed by expanding the Python
# block to include up to two additional arguments.  Note that the
# turtle is moved to the bottom of the block after it is loaded in
# order position another block to the bottom of the stack.

# For example, try the following to place forward 100, right 90 on the canvas:
# start
# Python(forward, 100)  <-- Python load_block.py expanded to two arguments
# Python(right, 90)  <-- Python load_block.py expanded to two arguments


def myblock(tw, blkname):
    ''' Load a block on to the canvas '''

    from TurtleArt.tapalette import block_names, block_primitives, \
        special_names, content_blocks
    from TurtleArt.tautils import find_group

    def make_block(tw, name, x, y, defaults):
        x_pos = x + 20
        y_pos = y + 20
        tw._new_block(name, x_pos, y_pos, defaults)

        # Find the block we just created and attach it to a stack.
        tw.drag_group = None
        spr = tw.sprite_list.find_sprite((x_pos, y_pos))
        if spr is not None:
            blk = tw.block_list.spr_to_block(spr)
            if blk is not None:
                tw.drag_group = find_group(blk)
                tw._snap_to_dock()

        # Disassociate new block from mouse.
        tw.drag_group = None
        return blk.height

    def find_block(tw, blkname, x, y, defaults=None):
        """ Create a new block. It is a bit more work than just calling
        _new_block(). We need to:
        (1) translate the label name into the internal block name;
        (2) 'dock' the block onto a stack where appropriate; and
        (3) disassociate the new block from the mouse. """

        print blkname
        for name in block_names:
            # Translate label name into block/prim name.
            if blkname in block_names[name]:
                if (name in block_primitives and \
                        block_primitives[name] == name) or \
                        name in content_blocks:
                    return make_block(tw, name, x, y, defaults)
        for name in special_names:
            # Translate label name into block/prim name.
            if blkname in special_names[name]:
                return make_block(tw, name, x, y, defaults)
        return -1

    # Place the block at the active turtle (x, y) and move the turtle
    # into position to place the next block in the stack.
    x, y = tw.active_turtle.get_xy()
    if type(blkname) == type([]):
        name = blkname[0]
        value = blkname[1:]
        dy = int(find_block(tw, name, x, y, value))
    else:
        name = blkname
        dy = int(find_block(tw, name, x, y))

    tw.active_turtle.move((x, y - dy))