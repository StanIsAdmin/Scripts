class Cursor:
	"""
	Represents a pad cursor, located at a give row and column
	"""
	def __init__(self):
		self.row = -1
		self.col = -1
		
	def reset(self):
		"""
		Removes the cursor from the pad, without deleting it
		"""
		self.row = -1
		self.col = -1
		
	def isSynced(self):
		"""
		Returns True if the cursor is located in the pad, False otherwise
		"""
		return self.row != -1 and self.col != -1

class PadOutOfSync(Exception):
	"""
	Raised when the provided information is not relevant to the current pad content, and should be handled by re-syncinc the client content with the pad's.
	"""
	pass
	
class PadSelectionDenied(Exception):
	"""
	Raised when a cursor seek attempt has been denied because another cursor has already selected the same line. Should be handled by restoring the client's cursor position to its previous state.
	"""
	pass
	
class PadModificationDenied(Exception):
	"""
	Raised when an attempt to modify the pad content is denied. This can happen when a cursor that is out of sync is used to modify the pad.
	"""
	pass

class Pad:
	"""
	Represents a text area with any number of cursors located on different lines.
	Modifications of the text may be submitted along with a cursor identification as long as the cursor selection/position has been accepted.
	"""
	def __init__(self, text):
		self.file_path = file_path
		
		#Read initial content from file to a line list
		self.lines = list(text)
		
		self.content_as_string = "" #Whole content concatenated into one string
		self.content_was_modified = True #Was the content modified since the last concat ?
		
		#Cursor dict and value used for default cursor ids
		self.cursors = {}
		self.new_cursor_id = -1
		
	def _char_to_row_col(self, char_count):
		"""
		Translates an offset (in chars and from file beginning) to row, col position
		"""
		row, col = 0, 0
		
		while char_count > 0:
			#Current line lenght
			line_cols = len(self.lines[row])
			
			#If offset is located in this line, adjust column
			#(last line does not end in \n character, therefore cursor may go as far as last col)
			if char_count < line_cols or row == len(self.lines) - 1:
				col = char_count
				char_count = 0
			#If offset continues further, increment row and adjust column
			else:
				row += 1
				col = 0
				char_count -= line_cols
		
		return row, col
		
	def _row_col_to_char(self, row, col):
		"""
		Translates a (row, col) position into a char offset from file beginning.
		"""
		char = 0
		
		while row > 0:
			char += len(self.lines[row])
		
		return char + col
		
	def _get_cursor_from_id(self, cursor_id):
		try:
			return self.cursors[cursor_id]
		except:
			raise KeyError("cursor with id " + str(cursor_id) + " does not exist.")
		
	def _get_all_cursors(self):
		for cursor in self.cursors.values():
			yield cursor
			
	def _cursor_can_select_row(self, row_number, cursor_ref):
		"""
		Returns True if the line at 'row_number' is free of any cursor other than cursor_ref
		"""
		for cur in self._get_all_cursors():
			#If there is another cursor on 'row_number'
			if cur.row == row_number and cur != cursor_ref:
				return False
		return True
		
	def cursor_create(self, cursor_id=None):
		"""
		Creates a new cursor and returns its id, which is the same as cursor_id if provided.
		Note: if provided cursor_id is not unique, raises KeyError
		"""
		if cursor_id is None:
			#Find next available id
			while self.new_cursor_id in self.cursors:
				self.new_cursor_id += 1
			#Create cursor with that id
			self.cursors[self.new_cursor_id] = Cursor()
			return self.new_cursor_id
		
		else:
			#Check if provided cursor_id is not already used
			if cursor_id in self.cursors:
				raise KeyError("cursor id " + str(cursor_id) + " already exists.")
			#Create cursor with cursor_id
			self.cursors[cursor_id] = Cursor()
			return cursor_id
		
	def cursor_seek(self, cursor_id, seek_position, seek_context, context_offset):
		"""
		Positions cursor identified by 'cursor_id' at position 'seek_position', or at closest position where substring 'seek_context' was found in the text plus context_offset.
		- 'seek_context' must be at least one char long and is meant to represent the chars located before and after 'seek_position' in the client's text.
		- 'context_offset' is the number of context characters located to the left of 'seek_position').
		
		Raises PadOutOfSync if no position can be found that satisfies the provided information.
		Raises PadSelectionDenied if the cursor could not be moved to the required position
		"""
		text = repr(self) #Whole text as single string
		
		#If char position is not valid or if seek_context is longer than text, pad is out of sync
		if seek_position < 0 or seek_position < context_offset:
			raise ValueError("Seek position " + str(seek_position) + " is not valid.")
			
		if len(seek_context) > len(text) or len(seek_context)==0:
			self.cursor_reset(cursor_id)
			raise PadOutOfSync("Seek context lenght is not valid.")
		
		#Find next and previous closest positions of center of seek_context
		context_left_span = context_offset
		context_right_span = len(seek_context) - context_offset
		
		next_closest_position = text.find(seek_context, seek_position - context_left_span)
		prev_closest_position = text.rfind(seek_context, 0, seek_position + context_right_span)
		
		#If context could not be found, pad is out of sync
		if next_closest_position == -1 and prev_closest_position == -1:
			self.cursor_reset(cursor_id)
			raise PadOutOfSync("Seek context could not be found in text.")
		
		#Choose best position
		distance_to_next = (next_closest_position + context_left_span) - seek_position
		distance_to_prev = seek_position - (prev_closest_position + context_left_span)
		
		true_position = 0
		if prev_closest_position == -1 or distance_to_next < distance_to_prev:
			true_position = next_closest_position + context_left_span
		else:
			true_position = prev_closest_position + context_left_span
		
		#Translate position to row, col
		row, col = self._char_to_row_col(true_position)
		
		#Check if cursor is allowed to select chosen line
		cursor = self._get_cursor_from_id(cursor_id)
		if self._cursor_can_select_row(row, cursor):
			cursor.row, cursor.col = row, col
			return true_position
		else:
			raise PadSelectionDenied
		
		
	def cursor_delete(self, cursor_id):
		"""
		Removes the cursor identified by cursor_id from the Pad.
		"""
		cursor = self._get_cursor_from_id(cursor_id) #Check if cursor exists first
		del self.cursors[cursor_id]
		
	def cursor_reset(self, cursor_id):
		"""
		Resets the position of cursor identified by cursor_id so that it is no longer in the pad.
		"""
		cursor = self._get_cursor_from_id(cursor_id) #Check if cursor exists first
		cursor.reset()
		
	def insert(self, cursor_id, content):
		"""
		Inserts 'content' from the position of the cursor identified by 'cursor_id'.
		
		Raises PadModificationDenied if the cursor is not synced (not in a valid position).
		"""
		#Check if cursor exists and is in valid position
		cursor = self._get_cursor_from_id(cursor_id)
		if not cursor.isSynced():
			raise PadModificationDenied("Cursor selection is not in sync.")
		
		pad_line = self.lines[cursor.row]
		
		#Insert content into line
		self.content_was_modified = True
		self.lines[cursor.row] = pad_line[0:cursor.col] + content + pad_line[cursor.col:]
				
		#Check if line needs to be splitted (new lines)
		splitted_lines = self.lines[cursor.row].splitlines(keepends=True)
		
		#If no line feeds have been added, advance same-line cursors and return
		if len(splitted_lines) == 1:
			for other_cursor in self._get_all_cursors():
				if other_cursor.row == cursor.row and other_cursor.col >= cursor.col:
					other_cursor.col += len(content)
			return
		
		#Modify line list
		current_row = cursor.row #Modified row
		current_col = cursor.col #Modified column
		self.lines = self.lines[0:current_row] + splitted_lines + self.lines[current_row+1:]
		
		#Compute offset due to insertion (for futher cursors)
		furtherCursorRowOffset = len(splitted_lines) - 1
		furtherCursorColOffset = (len(content) - content.rindex('\n') - 1) - current_col
		
		#Advance cursors
		for other_cursor in self._get_all_cursors():
			#Cursors on following lines: advance row
			if other_cursor.row > current_row:
				other_cursor.row += furtherCursorRowOffset
			#Cursors on same line and following columns: advance row and columns
			elif other_cursor.row == current_row and other_cursor.col >= current_col:
				other_cursor.row += furtherCursorRowOffset
				other_cursor.col += furtherCursorColOffset
	
	
	def remove(self, cursor_id, backspace_count):
		"""
		Removes backspace_count characters from the cursor identified by cursor_id
		"""
		self.content_was_modified = True
		cursor = self._get_cursor_from_id(cursor_id)
		
		current_row = cursor.row
		current_col = cursor.col
		del_start_row = cursor.row
		del_start_col = cursor.col
		
		backspace_remaining = backspace_count
		backspace_stop = False
		
		while not backspace_stop:
			#If we ran out of backspaces
			if del_start_col > backspace_remaining:
				backspace_stop = True
				del_start_col = del_start_col - backspace_remaining
				backspace_remaining = 0
		
			#If we ran out of characters
			elif del_start_row == 0:
				backspace_stop = True
				backspace_remaining -= del_start_col
				del_start_col = 0
			
			#If we must continue
			else:
				backspace_remaining -= del_start_col
				#If cursor is allowed to select previous line
				if self._cursor_can_select_row(del_start_row-1, cursor):
					del_start_row -= 1
					del_start_col = len(self.lines[del_start_row])
				#Otherwise stop there
				else:
					del_start_col = 0
					backspace_stop = True
		
		#Row and column offsets after the deletion
		rows_offset = current_row - del_start_row
		cols_offset = del_start_col - current_col
		
		for cur in self._get_all_cursors():
			if cur.row > current_row:
				cur.row -= rows_offset
			elif cur.row >= current_row and cur.col >= current_col:
				cur.row -= rows_offset
				cur.col += cols_offset
				
		first_line = self.lines[del_start_row]
		last_line = self.lines[current_row]
		self.lines[del_start_row] = first_line[0:del_start_col] + last_line[current_col:]
		
		for i in range(1, rows_offset+1):
			del self.lines[del_start_row + 1]
		
	def printCursorPositions(self):
		for id, cur in self.cursors.items():
			print("Cursor n°", id, "row", cur.row, "col", cur.col, "pos", )

	def __repr__(self):
		if self.content_was_modified:
			self.content_was_modified = False
			self.content_as_string = ''.join(self.lines)
		return self.content_as_string
