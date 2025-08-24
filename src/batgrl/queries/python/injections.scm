((call
  function: (attribute
	  object: (identifier) @_re)
  arguments: (argument_list (string) @regex))
 (#eq? @_re "re")
 (#match? @regex "^r"))

((assignment
  left: (identifier)
  right: (string) @regex)
(#match? @regex "^r"))

(comment) @comment
