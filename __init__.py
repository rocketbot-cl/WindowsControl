# coding: utf-8
# pylint: disable=global-statement, import-error, wrong-import-position, self-assigning-variable, global-at-module-level, broad-exception-raised, global-variable-not-assigned
"""
Base para desarrollo de modulos externos.
Para obtener el modulo/Funcion que se esta llamando:
     GetParams("module")

Para obtener las variables enviadas desde formulario/comando Rocketbot:
    var = GetParams(variable)
    Las "variable" se define en forms del archivo package.json

Para modificar la variable de Rocketbot:
    SetVar(Variable_Rocketbot, "dato")

Para obtener una variable de Rocketbot:
    var = GetVar(Variable_Rocketbot)

Para obtener la Opcion seleccionada:
    opcion = GetParams("option")


Para instalar librerias se debe ingresar por terminal a la carpeta "libs"

    pip install <package> -t .

"""
# Rocketbot function and disable pylint warning
GetParams = GetParams  # pylint: disable=undefined-variable
GetVar = GetVar  # pylint: disable=undefined-variable
SetVar = SetVar  # pylint: disable=undefined-variable
PrintException = PrintException  # pylint: disable=undefined-variable
tmp_global_obj = tmp_global_obj  # pylint: disable=undefined-variable

import os.path
import traceback
import copy
from time import sleep
import json
import time
import sys

base_path = tmp_global_obj["basepath"]
cur_path = base_path + "modules" + os.sep + "WindowsControl" + os.sep + "libs" + os.sep
sys.path.append(cur_path)

global windowScope, ET, find_control_by_index_new
import xml.etree.ElementTree as ET
from r_uiautomation import uiautomation as auto



# global module
module = GetParams("module")

"""
    Resuelvo catpcha tipo reCaptchav2
"""

ProcessTime = time.perf_counter  # this returns nearly 0 when first call it if python version <= 3.6
ProcessTime()
time_delta = 0

def getSelector(Selector_):
    """Convierte el selector de Rocketbot a un selector de pywinauto"""
    new_command = {}
    try:
        if isinstance(Selector_, str):
            Selector_ = Selector_.replace("\\", "\\\\")
            tmp = json.loads(Selector_)
        else:
            tmp = Selector_

        if "handle_" in tmp and len(tmp) == 1:
            print("Only Handle connection")
            new_command["handle"] = tmp["handle_"]
        else:
            if "app" in tmp and len(str(tmp["app"])) > 0:
                new_command["path"] = tmp["app"]
            if "title" in tmp and len(str(tmp["title"])) > 0:
                new_command["Name"] = tmp["title"]
            if "ctrlId" in tmp and len(str(tmp["ctrlId"])) > 0:
                new_command["AutomationId"] = (
                    int(tmp["ctrlId"]) if tmp["ctrlId"].isdigit() else tmp["ctrlId"]
                )
            if "class" in tmp and len(str(tmp["class"])) > 0:
                new_command["ClassName"] = tmp["class"]
            if "idx" in tmp and len(str(tmp["idx"])) > 0:
                new_command["ctrl_index"] = int(tmp["idx"]) - 1
    except Exception as unknown_ex:
        PrintException()
        raise Exception("Error on Selector XML or JSON :" + str(unknown_ex)) from unknown_ex
    # print("command", command_)
    return new_command


def create_control(select, timeout=30, wait=False, only_index=False):
    """Crea un control de uiautomation a partir de un selector"""
    global ProcessTime, time_delta, get_selectors, find_control_by_index
    start = ProcessTime()

    # Creating new scope
    new_scope = None
    if (
        not only_index and
        len(select["children"]) > 1
        and select["children"][0]["ctrltype"] == "WindowControl"
    ):
        s = select["children"][0]
        if "cls" in select["children"][0]:
            s["class"] = select["children"][0]["cls"]
        del s["idx"]
        selector_win = getSelector(s)
        new_scope = windowScope.WindowControl(**selector_win)
        del select["children"][0]


    parent = select["children"][0]
    arguments = get_selectors(parent)
    first_valid_child = 0 if only_index else 1
    if only_index:
        parent_control = windowScope
    elif new_scope:
        parent_control = new_scope.Control(**arguments)
    else:
        parent_control = windowScope.Control(**arguments)

    if len(select["children"]) == 0:
        return parent_control

    if parent_control:
        if wait:
            exist_parent = parent_control.Exists2(timeout, 1)
        else:
            exist_parent = parent_control.Exists(timeout, 1)
        if exist_parent:
            time_delta = start + timeout - ProcessTime()
            # print(select)
            return find_control_by_index(parent_control, select["children"][first_valid_child:])
            # for i, child in enumerate(parent_control.GetChildren()):
            #     if i == position_child:
            #         return child


def find_control_by_index(parent_control, selectors):
    """Busca un control a partir de un indice"""
    for item in selectors:
        # print(f"Searching by: {get_selectors(item)}")
        children_control = parent_control.GetChildren()
        for index, child_control in enumerate(children_control):
            if index == item["idx"]:
                parent_control = child_control
    return parent_control


def find_control_by_direct_index(parent_control, index):
    """Busca un control hijo directo a partir de un indice entero."""
    return find_control_by_index_new(parent_control, index)


def find_control_by_index_new(parent_control, index):
    """Busca un control hijo directo por indice usando la ventana/parent actual."""
    if not parent_control:
        return None

    try:
        index = int(index)
    except Exception:
        return None

    children_control = parent_control.GetChildren()
    if index < 0 or index >= len(children_control):
        return None
    return children_control[index]


def find_control_by_index_path(parent_control, index_path):
    """Busca un control navegando una ruta de indices desde el parent actual."""
    if not parent_control:
        return None

    current_control = parent_control
    for raw_index in index_path:
        next_control = find_control_by_index_new(current_control, raw_index)
        if not next_control:
            return None
        current_control = next_control

    return current_control


def get_selectors(parent):
    arguments = {}
    if "ctrlid" in parent and parent["ctrlid"]:
        arguments["AutomationId"] = parent["ctrlid"]
    if "title" in parent and parent["title"]:
        arguments["Name"] = parent["title"]
    if "cls" in parent and parent["cls"]:
        arguments["ClassName"] = parent["cls"]
    if "ctrltype" in parent and parent["ctrltype"]:
        arguments["ControlTypeName"] = parent["ctrltype"]
    return arguments


def getChildren(window, Selector):
    global getSelector, ET
    """ Busca los hijos de la ventana"""
    da = []
    if str(Selector).startswith("<"):
        Selector = "<data>" + Selector + "</data>"
        da = ET.XML(Selector)
        for item in da:
            da.append(item)

    if str(Selector).startswith("{"):
        Selector = "[" + Selector + "]"
    if str(Selector).startswith("["):
        da = json.loads(Selector)
    # print("da", da)
    w = window.child_window(**getSelector(da[0])).wait("visible", timeout=20)
    # print("DA", da)
    if len(da[1:]) > 0:
        for item in da[1:]:
            try:
                w = w.child_window(**getSelector(item)).wait("visible", timeout=20)
            except Exception as e:
                print("error w", e)
                PrintException()
                raise Exception(e)
    # print("w", w)
    return w


def get_position(control, ratioX: float = 0.5, ratioY: float = 0.5):
    rect = control.BoundingRectangle
    x = rect.left + int(rect.width() * ratioX)
    y = rect.top + int(rect.height() * ratioY)
    return x, y


try:
    # CamelCase notation for common params
    Selector = GetParams("Selector")
    OnlyIndex = GetParams("onlyIndex") == "True"
    selector = None

    if module == "WindowScope":
        windowScope = None
        TimoutMS = GetParams("TimeoutMS")
        var_ = GetParams("result")
        timeout_ = 30
        command_ = ""
        app = None

        result = False

        try:
            try:
                if len(str(TimoutMS).strip()) > 0:
                    timeout_ = int(TimoutMS)
            except:
                pass
            command_ = getSelector(Selector)
            if len(str(command_)) > 1:
                windowScope = auto.WindowControl(**command_)
                try:
                    result = windowScope.ExistsWindow(timeout_, 1)
                except:
                    result = windowScope.Exists(timeout_, 1)
                if result:
                    windowScope.SetFocus()
                    # windowScope.top_window().print_control_identifiers()
            else:
                raise Exception("No Selector")
            SetVar(var_, result)
        except Exception as e:
            print("\x1B[" + "31;40mAn error occurred\x1B[" + "0m")
            PrintException()
            SetVar(var_, False)
    
    # If the module is not WindowScope, we need to create a different selector
    elif module not in ("GetHandle", "AdvancedWindowControl", "clickporIndex", "envioTeclas", "enviosTeclas"):
        if Selector is None or len(str(Selector).strip()) < 1:
            raise Exception("The field 'Selector' is empty and it is required")
        try:
            selector = eval(Selector)
        except Exception as ex:
            raise Exception("Error on Selector XML or JSON :" + str(ex)) from ex

        control = create_control(selector, only_index=OnlyIndex)

    if module == "Screenshot":
        path_ = GetParams("path_screenshot")
        try:
            windowScope.SetFocus()
            control.CaptureToImage(path_)

        except Exception as e:
            print("\x1B[" + "31;40mAn error occurred\x1B[" + "0m")
            PrintException()
            raise e

    if module == "GetValue":
        var_ = GetParams("result")
        timeout_ = 30
        try:
            # if not control_by:
            #     control_by = "ctrlid"
            className = selector["parent"]["cls"]
            windowScope.SetFocus()
            try:
                if control.ControlTypeName == "DataItemControl":
                    currentValue = control.GetLegacyIAccessiblePattern().Value
                else:
                    currentValue = control.GetPattern(10002).Value
            except:
                currentValue = control.GetWindowText()
            if currentValue is None:
                currentValue = control.Name

            SetVar(var_, str(currentValue))
        except Exception as e:
            print("\x1B[" + "31;40mAn error occurred\x1B[" + "0m")
            PrintException()
            raise e

    if module == "SetValue":
        var_ = GetParams("result")
        Text = GetParams("Text")
        clean = GetParams("Clean")
        timeout_ = 30

        if (
            "mozilla" in selector["parent"]["cls"].lower()
            or "chrome" in selector["parent"]["cls"].lower()
        ):
            className = selector["children"][0]["cls"]
        else:
            className = selector["parent"]["cls"]
        try:
            control = create_control(selector)
            windowScope.SetFocus()
            clean = eval(clean) if clean is not None else False
            if not clean:
                try:
                    currentValue = control.GetPattern(10002).Value
                    # print(currentValue, "--------")
                except:
                    print("exception")
                    currentValue = control.GetWindowText()

                if currentValue:
                    # print(currentValue)
                    Text = currentValue + Text

            try:
                # print(dir(control))
                control.GetPattern(auto.PatternId.ValuePattern).SetValue(Text)
            except:
                print("-----------")
                control.SetWindowText(Text)
        except Exception as e:
            print("\x1B[" + "31;40mAn error occurred\x1B[" + "0m")
            PrintException()
            raise e

    if module == "SelectItem":
        var_ = GetParams("result")
        Item = GetParams("Item")
        timeout_ = 30
        result_ = False

        try:
            if str(Item).isnumeric():
                Item = int(Item)

            windowScope.SetFocus()

            # print(dir(control))
            control.GetLegacyIAccessiblePattern().SetValue(Item)
            # control.GetPattern().SetValue(Item)
            SetVar(var_, str(result_))
        except Exception as e:
            print("\x1B[" + "31;40mAn error occurred\x1B[" + "0m")
            PrintException()
            raise e

    if module == "Click":
        timeout_ = 30
        command_ = ""
        result_ = False
        simulateclick_ = False
        mousebutton_ = "left"
        double_ = False
        button_down = True
        button_up = True
        var_ = GetParams("result")
        TimoutMS = GetParams("TimeoutMs")
        SimulateClick = GetParams("SimulateClick")
        MouseButton = GetParams("MouseButton")
        ClickType = GetParams("ClickType")

        try:

            if not SimulateClick is None:
                simulateclick_ = SimulateClick

            if not ClickType == None:
                if ClickType == "CLICK_DOUBLE":
                    double_ = True
                if ClickType == "CLICK_DOWN":
                    button_up = False
                if ClickType == "CLICK_UP":
                    button_down = False

            if len(str(Selector)) > 1:
                try:
                    windowScope.SetFocus()

                    if ClickType != "CLICK_DOUBLE":
                        if MouseButton == "BTN_LEFT":
                            control.Click(simulateMove=simulateclick_, waitTime=0.5)
                        if MouseButton == "BTN_RIGHT":
                            control.RightClick(simulateMove=simulateclick_)
                        if MouseButton == "BTN_MIDDLE":
                            control.MiddleClick(simulateMove=simulateclick_)
                    else:
                        control.DoubleClick(simulateMove=simulateclick_, waitTime=0.5)
                    result_ = True
                except Exception as e:
                    SetVar(var_, False)
                    PrintException()
                    raise e

                SetVar(var_, True)
        except Exception as e:
            SetVar(var_, False)
            PrintException()
            raise e

    if module == "Relative_click":
        x_coord = int(GetParams("x_coord"))
        y_coord = int(GetParams("y_coord"))

        try:
            windowScope.SetFocus()

            # control.MoveCursorToInnerPos(x=x_coord, y=y_coord)
            x, y = control.MoveCursorToMyCenter()

            x_coord += x
            y_coord += y

            time.sleep(1)
            auto.Click(x=x_coord, y=y_coord, waitTime=0.5)

        except Exception as e:
            PrintException()
            raise e

    if module == "waitObject":
        var_ = GetParams("result")
        type_ = GetParams("type")
        timeout_ = GetParams("TimeoutMS")
        result_ = False

        try:

            if timeout_:
                timeout_ = float(timeout_)
            else:
                timeout_ = float(30)
            auto.TIME_OUT_SECOND = 10

            if type_ == "disappears":
                control = create_control(selector, 5, only_index=OnlyIndex)
                if time_delta != 0:
                    timeout_ = timeout_ + time_delta - 5
                if control:
                    # print(control, time_delta)
                    result_ = control.Disappears(timeout_, 1)
                else:
                    result_ = True
            else:
                control = create_control(selector, timeout_, wait=True, only_index=OnlyIndex)
                if time_delta != 0:
                    timeout_ = time_delta
                try:
                    result_ = control.Exists2(timeout_, 1)
                except:
                    result_ = control.Exists(timeout_, 1)

            if var_:
                SetVar(var_, result_)

        except Exception as e:
            SetVar(var_, result_)
            PrintException()

    if module == "SendKeys":
        var_ = GetParams("result")
        delay = GetParams("delay")
        Text = GetParams("Text")
        timeout_ = 30

        try:

            if (
                "mozilla" in selector["parent"]["cls"].lower()
                or "chrome" in selector["parent"]["cls"].lower()
            ):
                className = selector["children"][0]["cls"]
            else:
                className = selector["parent"]["cls"]
            control.SetFocus()
            sleep(1)
            control.SendKeys(Text)
            if delay:
                sleep(int(len(Text) / 4))
            SetVar(var_, True)
        except Exception as e:
            PrintException()
            SetVar(var_, False)
            raise e

    if module == "Wheel":
        times = GetParams("times")
        type_ = GetParams("type")
        var_ = GetParams("result")
        timeout_ = 30

        try:

            if not times:
                times = 1
            else:
                times = int(times)

            if (
                "mozilla" in selector["parent"]["cls"].lower()
                or "chrome" in selector["parent"]["cls"].lower()
            ):
                className = selector["children"][0]["cls"]
            else:
                className = selector["parent"]["cls"]
            control = create_control(selector)
            windowScope.SetFocus()
            if type_ == "up":
                control.WheelUp(wheelTimes=times)
            else:
                control.WheelDown(wheelTimes=times)
            SetVar(var_, True)
        except Exception as e:
            PrintException()
            SetVar(var_, False)
            raise e

    if module == "ExtractTable":
        var_ = GetParams("result")
        row_index = GetParams("row_index")
        col_index = GetParams("col_index")
        timeout_ = 30
        try:

            className = selector["parent"]["cls"]
            control = create_control(selector)
            windowScope.SetFocus()
            if control.ControlTypeName in ("TableControl", "PaneControl"):
                currentValue = []
                for row in control.GetChildren():
                    rows = []
                    for cell in row.GetChildren():
                        rows.append(cell.GetLegacyIAccessiblePattern().Value)

                    currentValue.append(rows)

                if row_index:
                    currentValue = currentValue[row_index]
                    if col_index:
                        currentValue = currentValue[col_index]
                SetVar(var_, currentValue)
            else:
                raise Exception("Control type must be TableControl")

        except Exception as e:
            PrintException()
            raise e

    if module == "GetHandle":
        import win32gui

        result = GetParams("var")
        filter_ = GetParams("filter")

        try:
            handleInfo = []

            def winEnumHandler(hwnd, ctx):
                global handleInfo
                if win32gui.IsWindowVisible(hwnd):
                    handleInfo.append((hwnd, win32gui.GetWindowText(hwnd)))

            win32gui.EnumWindows(winEnumHandler, None)

            handle_info = []
            for h in handleInfo:
                if (
                    filter_.startswith("*")
                    and filter_.endswith("*")
                    and filter_[1:-1] in h[1]
                ):
                    handle_info.append(h)
                elif filter_.startswith("*") and h[1].endswith(filter_[1:]):
                    handle_info.append(h)
                elif filter_.endswith("*") and h[1].startswith(filter_[:-1]):
                    handle_info.append(h)
                elif not filter_:
                    handle_info.append(h)

            SetVar(result, handle_info)
        except Exception as e:
            print("\x1B[" + "31;40mError\x1B[" + "0m")
            PrintException()
            raise e

    if module == "ReadList":
        var_ = GetParams("result")
        try:
            windowScope.SetFocus()
            if control.ControlTypeName == "ListControl":
                currentValue = []
                for row in control.GetChildren():
                    rows = []
                    for cell in row.GetChildren():
                        rows.append(cell.GetLegacyIAccessiblePattern().Name)

                    currentValue.append(rows)
                SetVar(var_, currentValue)
            else:
                raise Exception("Control type must be ListControl")

        except Exception as e:
            PrintException()
            raise e

    if module == "findChildren":
        data = GetParams("data")
        find_by = GetParams("findBy")
        result = GetParams("result")

        try:
            windowScope.SetFocus()

            children = []
            for i, child in enumerate(control.GetChildren()):
                if getattr(child, find_by) == data:
                    # {"ctrlid":"NumberPad","cls":"NamedContainerAutomationPeer","title":"Teclado numérico","ctrltype":"GroupControl","idx": 7}
                    child_selector = {}
                    if child.AutomationId:
                        child_selector["ctrlid"] = child.AutomationId
                    if child.ClassName:
                        child_selector["cls"] = child.ClassName
                    if child.Name:
                        child_selector["title"] = child.Name
                    if child.ControlTypeName:
                        child_selector["ctrltype"] = child.ControlTypeName
                    child_selector["idx"] = i
                    children.append(child_selector)

            SetVar(result, children)

        except Exception as e:
            print("\x1B[" + "31;40mAn error occurred\x1B[" + "0m")
            PrintException()
            raise e

    if module == "readCheckbox":

        result = GetParams("result")
        variant = GetParams("variant")

        try:
            if variant is not None:
                variant = eval(variant)

            windowScope.SetFocus()
            if control.ControlTypeName != "CheckBoxControl":
                raise Exception("Object is not CheckBoxControl")

            if not variant:
                default_action = control.GetLegacyIAccessiblePattern().DefaultAction
            else:
                default_action = control.GetLegacyIAccessiblePattern().Value

            if result:
                SetVar(result, default_action)
        except Exception as e:
            print("\x1B[" + "31;40mAn error occurred\x1B[" + "0m")
            PrintException()
            raise e

    if module == "isEnable":
        result = GetParams("result")

        windowScope.SetFocus()

        isEnabled = control.IsEnabled
        # print("result", result, isEnabled)
        if result:
            SetVar(result, bool(isEnabled))

    if module == "DragAndDrop":
        source_selector = GetParams("source_selector")
        destination_selector = GetParams("destination_selector")
        source_coordinates = GetParams("source_coordinates")
        destination_coordinates = GetParams("destination_coordinates")
        result = GetParams("result")
        SetVar(result, False)

        source_control = destination_control = None

        if source_coordinates:
            x1, y1 = eval(source_coordinates)

        if destination_coordinates:
            x2, y2 = eval(destination_coordinates)

        if source_selector:
            source_selector = json.loads(source_selector)
            source_control = create_control(source_selector)
            x1, y1 = get_position(source_control)

        if destination_selector:
            destination_selector = json.loads(destination_selector)
            destination_control = create_control(destination_selector)
            x2, y2 = get_position(destination_control)

        windowScope.SetFocus()
        auto.DragDrop(x1, y1, x2, y2)
        SetVar(result, True)

    if module == "GetPosition":
        move = GetParams("move")
        result = GetParams("result")
        if move and move == "True":
            x, y = control.MoveCursorToMyCenter(simulateMove=True)
        else:
            x, y = get_position(control)

        SetVar(result, (x, y))

    if module == "AdvancedWindowControl":

        window_name = GetParams("window_name")
        action = GetParams("action")
        control = auto.WindowControl(Name=window_name, ControlTypeName="WindowControl")
        pattern = control.GetWindowPattern()
        if action == "close":
            pattern.Close()
        elif action == "maximize":
            pattern.SetWindowVisualState(auto.WindowVisualState.Maximized)
        elif action == "minimize":
            pattern.SetWindowVisualState(auto.WindowVisualState.Minimized)
        elif action == "restore":
            pattern.SetWindowVisualState(auto.WindowVisualState.Normal)
            
            
    if module == "clickporIndex":
        ir_a_index = GetParams("go_to_index")
        var_ = GetParams("result")

        try:
            index_path = None
            if isinstance(ir_a_index, list):
                index_path = ir_a_index
            else:
                raw_index = str(ir_a_index).strip()
                if raw_index.startswith("[") and raw_index.endswith("]"):
                    index_path = json.loads(raw_index)
                else:
                    index_path = [int(raw_index)]

            if not isinstance(index_path, list) or len(index_path) == 0:
                raise Exception("ir_a_index must be an integer or a list of indices")

            index_path = [int(i) for i in index_path]

            if not windowScope:
                raise Exception("There is no connected window. Run WindowScope before clickbyIndex")

            control = find_control_by_index_path(windowScope, index_path)

            if not control:
                SetVar(var_, False)
                raise Exception("The control for the index or index path sent could not be found.")

            windowScope.SetFocus()
            try:
                control.SetFocus()
            except Exception:
                pass

            try:
                if hasattr(control, 'Invoke'):
                    control.Invoke()
                else:
                    
                    control.Click(simulateMove=False, waitTime=0.5)
            except Exception:
                
                rect = control.BoundingRectangle
                auto.Click(rect.centerX(), rect.centerY())

            if texto:
                control.SendKeys(texto)

            if tecla_enviar and str(tecla_enviar).strip():
                tecla = str(tecla_enviar).strip()
                if not (tecla.startswith("{") and tecla.endswith("}")):
                    tecla = "{" + tecla + "}"
                control.SendKeys(tecla)

            SetVar(var_, True)
        
        except Exception as e:
            SetVar(var_, False)
            PrintException()
            raise e

    if module == "envioTeclas":
        enviar_texto =GetParams("send_text")
        enviar_tecla = GetParams("send_key")
        ir_a_index = GetParams("go_to_index")
        var_ = GetParams("result")

        try:
            index_path = None
            if isinstance(ir_a_index, list):
                index_path = ir_a_index
            else:
                raw_index = str(ir_a_index).strip()
                if raw_index.startswith("[") and raw_index.endswith("]"):
                    index_path = json.loads(raw_index)
                else:
                    index_path = [int(raw_index)]

            if not isinstance(index_path, list) or len(index_path) == 0:
                raise Exception("go to index must be an integer or a list of indices")

            index_path = [int(i) for i in index_path]

            if not windowScope:
                raise Exception("There is no connected window. Run WindowScope before envioTeclas")

            control = find_control_by_index_path(windowScope, index_path)

            if not control:
                SetVar(var_, False)
                raise Exception("The control for the index or index path sent could not be found.")

            windowScope.SetFocus()
            try:
                control.SetFocus()
            except Exception:
                pass

            if enviar_texto and str(enviar_texto):
                control.SendKeys(str(enviar_texto))

            if enviar_tecla and str(enviar_tecla).strip():
                tecla = str(enviar_tecla).strip()
                if not (tecla.startswith("{") and tecla.endswith("}")):
                    tecla = "{" + tecla + "}"
                control.SendKeys(tecla)

            SetVar(var_, True)

        except Exception as e:
            SetVar(var_, False)
            PrintException()
            raise e


    
            
except Exception as e:
    traceback.print_exc()
    PrintException()
    raise e
