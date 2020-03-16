"""A class for making building tkinter Widgets easier."""

from tkinter import *
from typing import List, Tuple, Union, Any
from .extraUtils import removeFromDict

def writable(target) -> bool:
    """Check if target is writable"""

    targetClass = target.__class__
    return not (issubclass(targetClass, Widget) or issubclass(targetClass, Wm))


class WidgetFactory:
    """
    Class to define the default settings for the factories.
    Essentially CSS for tkinter. The defaultAttrs (style sheet) can be overridden
    when calling a builder (inline CSS).
    
    ATTRIBUTES
    defaultAttrs: dict
        The default settings that are overridden at instantiation.
        These are applied unless overridden by the builders
    name: str
        A descriptive name for the instance (E.G 'Dark Theme').
    _passedFromBuilder: dict
        kwargs transferred from the default builder to the more rich builders.
    """

    # ATTRIBUTES
    _passedFromBuilder = {}

    #attributes
    defaultAttrs={
        'labelText': None,
        'command': None,
        'borderwidth': 0,
        'master': None,
        'fg': "white",
        'bg': "black",
        'text': None,
        'anchor': None,
        'relative': None,
        'sticky': None, 
        'relheight' : None,
        'relwidth' : None,
        }

    def __init__(self, name: str = "", **kwargs):
        '''Pass in any settings that should be applied by default by the builders
        
        name: 
            A desciptive name for the instance.'''

        self.name = name

        #override the default attrs
        for attr in list(kwargs.keys()):
            self.defaultAttrs[attr]=kwargs[attr]


    def setToDefaults(self, kwargsDict: dict):
        '''Checks if the defaults have been overridden, 
        if not then sets them to default and returns as a
        dict of variable name : value

        kwargsDict: dictionary of keyword arguments.'''

        #will store all  pairs
        arguments={}

        #create list of names of variables where variable=None
        #append input dict to arguments
        isNone=[]
        for key in kwargsDict:
            if kwargsDict[key] is None:
                isNone.append(key)
                
            else:
                arguments[key]=kwargsDict[key]

        #check if a default value for it is stored
        for key in isNone:
            try:
                arguments[key]=self.defaultAttrs[key]

            except KeyError:  #ignore unknown keys
                pass

        #append all default values to dict if not already given a value
        for key, value in self.defaultAttrs.items():
            if key not in arguments.keys():
                arguments[key]=value

        return arguments


    def generalBuilder(self, type: Widget, coords: tuple,
        *args: tuple, ignore: List[str] = [], **kwargs) -> Union[Widget, Tuple[Label, Widget]]:

        '''Factory to create most widgets with common arguments. 

        Use .config() on the results of this method to add extra attributes.
        Returns Widgets as a tuple as either (widget) or (label, widget)
        Not compatible with OptionMenu and Frame.

        Widget Attribute Arguments:
        type: tkinter widget class.
        co-ords: tuple of floats (x, y) to place the widget at.
        ignore: the keys of defaultAttrs to not apply.

        KWARGS:
        labelText: text for a label to be placed at co-ords(x, y-20).
        command: anonymous function to activate upon click of widget.
        create an anonymous function inline like this:
        command=lambda: func(args)
        borderwidth: float for the border size.
        master: Tk object to place the widget in.
        height: float height of the widget.
        width: float width of the widget.
        fg: string foreground colour.
        bg: string background colour.
        
        Placement Arguments:
        anchor: string anchor point.
        relative: boolean to define whether co-ords are relative.
        sticky: string sticky cardinal direction. These are inverted.
        relheight: height relative to the screen.
        relwidth: width relative to the screen.
        
        THROWS
        KeyError: if a default setting has been removed from WidgetFactory.defaultAttrs
        '''

        #this function assumes that no elements will be removed from
        #WidgetFactory.defaultAttrs
        
        newWidget= self.builder(type, *args, ignore = ignore, **kwargs)
        kwargsDict = self._passedFromBuilder

        placeParams = removeFromDict(kwargsDict, ("labelText", "command", "borderwidth",
            "master", "height", "width", "fg", "bg", "relative", "text"))

        for badParam in ("relheight", "relwidth"):  # these cause problems if passed as None
            if not placeParams[badParam]:
                del placeParams[badParam]

        #if labelText has a value, place a label at x, y-20
        if kwargsDict["labelText"]:
            #getting rid of incompatible kwargs
            labelParams=removeFromDict(kwargsDict, ["command", "text", "relative", "sticky"])

            #retrieving label text which is not compatible with label
            labelText=labelParams.pop("labelText")

            newLabel = Label(text =labelText, **labelParams)

            #if relative, place at y - 20% of y
            if kwargsDict["relative"]:
                newLabel.place(relx = coords[0], rely = coords[1] -(coords[1]*0.2), **placeParams)
            else:
                newLabel.place(x = coords[0], y = (coords[1]-20), **placeParams)

        #placing the widget
        if kwargsDict["relative"]:
            newWidget.place(relx = coords[0], rely = coords[1], **placeParams)

        else:
            newWidget.place(x = coords[0], y = coords[1], **placeParams)

        if kwargsDict["labelText"]:
            return (newLabel, newWidget)

        else:
            return (newWidget)


    def builder(self, type: Widget, *args: tuple, ignore: List[str] = [], **kwargs) -> Widget:
        """A stripped down version of generalBuilder (no placing or labels).
        Allows discarding of defaults for better compatibility.
        
        ignore: keys of self.defaultAttrs to not apply
        """    

        #expands the dictionary into kwargs again (key = value)
        newWidget=type(*args, **self._parseKeys(kwargs, ignore))

        return newWidget


    def _parseKeys(self, kwargs: dict, ignore: List[str]) -> dict:
        """Get a dict of kwargs ready to apply to a widget in a builder.
        Sets to defaults and removes ignore from it"""

        #set any NoneType kwargs to their defaults
        kwargsDict=self.setToDefaults(kwargs)

        #removing inconpatible params
        toRemove = set((["anchor", "sticky", "relative", "labelText",
            "relheight", "relwidth"] + ignore))  # ensure no duplicates
        widgetParams=removeFromDict(kwargsDict, toRemove)

        self._passedFromBuilder = kwargsDict

        return widgetParams


    def optionBuilder(self, var: Union[IntVar, DoubleVar, StringVar, BooleanVar],
        options: list, initialValue: Any = None, *args: tuple, ignore: List[str] = [], **kwargs) -> OptionMenu:
        """
        OptionMenu-compatible builder
        
        var:
            tkinter variable to hold the selection of the OptionMenu.
            Its value should be set to the initial value.
            ^ the builder can't do it without activating the observers.
        options:
            The available options.
        initialValue:
            The initially selected value.
            """

        if not initialValue:
            initialValue = options.pop(0)

        widgetParams = self._parseKeys(kwargs, (ignore + ["master", ]))

        menu = OptionMenu(self.defaultAttrs["master"], var, initialValue, *options)
        menu.config(*args, **widgetParams)  # OptionMenu throws errors when you pass settings @instantiation

        return menu


    def makeWritable(self) -> dict: 
        """Convert all attributes to serializable form.
        NOTE: master is removed.
        
        RETURNS
        dict of all attributes. Use makeUnwritable() to convert back"""

        # iterate over factory attrs and discard Widgets
        writableForm = {}
        for key, value in self.defaultAttrs.items():
            if writable(value):
                writableForm[key] = value

        # include name
        writableForm["name"] = self.name

        return writableForm