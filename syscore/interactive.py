import datetime
import sys
import time
from copy import copy

from syscore.dateutils import (
    n_days_ago,
    calculate_start_and_end_dates,
    get_date_from_period_and_end_date,
)
from syscore.genutils import str2Bool
from syscore.objects import arg_not_supplied


def get_field_names_for_named_tuple(named_tuple_instance):
    original_tuple_as_dict = named_tuple_as_dict(named_tuple_instance)
    for key_name in original_tuple_as_dict.keys():
        original_tuple_entry = original_tuple_as_dict[key_name]
        original_tuple_entry_class = original_tuple_entry.__class__
        input_result = get_and_convert(
            key_name,
            default_value=original_tuple_entry,
            type_expected=original_tuple_entry_class,
        )

        original_tuple_as_dict[key_name] = input_result

    new_tuple = override_tuple_fields(named_tuple_instance, original_tuple_as_dict)

    return new_tuple


def get_and_convert(
    prompt, type_expected=int, allow_default=True, default_value=0, default_str=None
):
    invalid = True
    input_str = prompt + " "
    if allow_default:
        if default_str is None:
            input_str = input_str + "<RETURN for default %s> " % str(default_value)
        else:
            input_str = input_str + "<RETURN for %s> " % default_str

    while invalid:
        ans = input(input_str)

        if ans == "" and allow_default:
            return default_value
        try:
            if type_expected is bool:
                result = str2Bool(ans)
            else:
                result = type_expected(ans)
            return result
        except BaseException:
            print("%s is not of expected type %s" % (ans, type_expected.__name__))
            continue


TOP_LEVEL = -1


class run_interactive_menu(object):
    def __init__(
        self,
        top_level_menu_of_options,
        nested_menu_of_options,
        exit_option=-1,
        another_menu=-2,
    ):
        """

        :param top_level_menu_of_options: A dict of top level options
        :param nested_menu_of_options: A dict of nested dicts, top levels keys are keys in top_level
        :return: object
        """

        self._top_level = top_level_menu_of_options
        self._nested = nested_menu_of_options
        self._location = TOP_LEVEL
        self._exit_option = exit_option
        self._another_menu = another_menu

    def propose_options_and_get_input(self):
        is_top_level = self._location == TOP_LEVEL
        if is_top_level:
            top_level_menu = self._top_level
            result = print_menu_and_get_response(
                top_level_menu, default_option=-1, default_str="EXIT"
            )
            if result == -1:
                return self._exit_option
            else:
                self._location = result
                return self._another_menu
        else:
            sub_menu = self._nested[self._location]
            result = print_menu_and_get_response(
                sub_menu, default_option=-1, default_str="Back"
            )
            if result == -1:
                self._location = -1
                return self._another_menu
            else:
                return result


def print_menu_of_values_and_get_response(menu_of_options_as_list, default_str=""):

    copy_menu_of_options_as_list = copy(menu_of_options_as_list)
    if default_str != "":
        try:
            copy_menu_of_options_as_list.index(default_str)
        except ValueError:
            copy_menu_of_options_as_list.append(default_str)

        default_option = copy_menu_of_options_as_list.index(default_str)
    else:
        default_option = None

    menu_of_options = dict(
        [
            (int_key, menu_value)
            for int_key, menu_value in enumerate(copy_menu_of_options_as_list)
        ]
    )
    ans = print_menu_and_get_response(
        menu_of_options, default_option=default_option, default_str=default_str
    )
    option_chosen = copy_menu_of_options_as_list[ans]

    return option_chosen


def print_menu_and_get_response(menu_of_options, default_option=None, default_str=""):
    """

    :param copy_menu_of_options: A dict, keys are ints, values are str
    :param default_option: None, or one of the keys
    :return: int menu chosen
    """
    copy_menu_of_options = copy(menu_of_options)
    menu_options_list = sorted(copy_menu_of_options.keys())
    for option in menu_options_list:
        print("%d: %s" % (option, copy_menu_of_options[option]))
    print("\n")
    computer_says_no = True
    if default_option is None:
        allow_default = False
    else:
        allow_default = True
        menu_options_list = [default_option] + menu_options_list

    while computer_says_no:
        ans = get_and_convert(
            "Your choice?",
            default_value=default_option,
            type_expected=int,
            allow_default=allow_default,
            default_str=default_str,
        )
        if ans not in menu_options_list:
            print("Not a valid option")
            continue
        else:
            computer_says_no = False
            break

    return ans


def true_if_answer_is_yes(prompt="", allow_empty_to_return_none=False) -> bool:
    invalid = True
    while invalid:
        x = input(prompt)
        if allow_empty_to_return_none:
            if x == "":
                return None

        x = x.lower()
        if len(x) > 0 and x[0] == "y":
            return True
        elif len(x) > 0 and x[0] == "n":
            return False
        print("Need one of yes/no, Yes/No, y/n, Y/N")


def get_report_dates():

    end_date = arg_not_supplied
    start_date = arg_not_supplied
    start_period = arg_not_supplied
    end_period = arg_not_supplied

    input_end_date = get_datetime_input(
        "End date for report?\n",
        allow_default=True,
        allow_period=True,
        allow_calendar_days=True,
    )

    if type(input_end_date) is int:
        ## calendar days
        end_date = n_days_ago(input_end_date, datetime.datetime.now())
    elif type(input_end_date) is str:
        ## period
        end_period = input_end_date
    elif type(input_end_date) is datetime.datetime:
        end_date = input_end_date
    else:
        raise Exception("Don't recognise %s" % str(input_end_date))

    input_start_date = get_datetime_input(
        "Start date for report? \n",
        allow_default=False,
        allow_period=True,
        allow_calendar_days=True,
    )

    if type(input_start_date) is int:
        ## calendar days
        start_date = n_days_ago(input_start_date, end_date)
    elif type(input_start_date) is str:
        ## period
        start_period = input_start_date
    elif type(input_start_date) is datetime.datetime:
        start_date = input_start_date
    else:
        raise Exception("Don't recognise %s" % str(input_start_date))

    start_date, end_date = calculate_start_and_end_dates(
        calendar_days_back=arg_not_supplied,
        end_date=end_date,
        start_date=start_date,
        start_period=start_period,
        end_period=end_period,
    )

    return start_date, end_date


def get_datetime_input(
    prompt: str,
    allow_default: bool = True,
    allow_calendar_days: bool = False,
    allow_period: bool = False,
):
    invalid_input = True
    input_str = (
        prompt
        + ": Enter date and time in format %Y-%m-%d eg '2020-05-30' OR '%Y-%m-%d %H:%M:%S' eg '2020-05-30 14:04:11'"
    )
    if allow_calendar_days:
        input_str = input_str + "\n OR [Enter a number to back N calendar days]"
    if allow_period:
        input_str = input_str + "OR [Enter a string for period, eg 'YTD', '3M', '2B']"
    if allow_default:
        input_str = input_str + "OR <RETURN for now>"

    while invalid_input:
        ans = input(input_str)
        if ans == "" and allow_default:
            return datetime.datetime.now()

        if allow_period:
            try:
                _NOT_USED = get_date_from_period_and_end_date(ans)
                ## all good, return as string
                return ans
            except:
                pass

        if allow_calendar_days:
            try:
                attempt_as_int = int(ans)
                return attempt_as_int
            except:
                pass

        try:
            ans = resolve_datetime_input_str(ans)
            return ans
        except:
            print("%s is not any valid input string" % ans)
            pass


def resolve_datetime_input_str(ans):
    if len(ans) == 10:
        return_datetime = datetime.datetime.strptime(ans, "%Y-%m-%d")
    elif len(ans) == 19:
        return_datetime = datetime.datetime.strptime(ans, "%Y-%m-%d %H:%M:%S")
    else:
        # problems formatting will also raise value error
        raise ValueError
    return return_datetime


PROGRESS_EXP_FACTOR = 0.9


class progressBar(object):
    """
    Example (not docstring as won't work)

    import time
    thing=progressBar(10000)
    for i in range(10000):
         # do something
         time.sleep(0.001)
         thing.iterate()
    thing.finished()

    """

    def __init__(
        self,
        range_to_iter,
        suffix="Progress",
        toolbar_width=80,
        show_each_time=False,
        show_timings=True,
    ):

        self._start_time = time.time()
        self.toolbar_width = toolbar_width
        self.current_iter = 0
        self.suffix = suffix
        self.range_to_iter = range_to_iter
        self.range_per_block = range_to_iter / float(toolbar_width)
        self._how_many_blocks_displayed = -1  # will always display first time
        self._show_each_time = show_each_time
        self._show_timings = show_timings

        self.display_bar()

    def estimated_time_remaining(self):
        total_iter = self.range_to_iter
        iter_left = total_iter - self.current_iter
        time_per_iter = self.current_estimate_of_times
        if time_per_iter is None:
            return 0

        return iter_left * time_per_iter

    def update_time_estimate(self):
        ## don't maintain a list per se, instead exponential
        time_since_last_call = self.time_since_last_called()
        current_estimate = self.current_estimate_of_times
        if current_estimate is None:
            ## seed
            current_estimate = time_since_last_call
        else:
            current_estimate = ((1 - PROGRESS_EXP_FACTOR) * time_since_last_call) + (
                PROGRESS_EXP_FACTOR * current_estimate
            )

        self.current_estimate_of_times = current_estimate

    @property
    def current_estimate_of_times(self) -> float:
        current_estimate = getattr(self, "_current_estimate_of_times", None)
        return current_estimate

    @current_estimate_of_times.setter
    def current_estimate_of_times(self, current_estimate: float):
        self._current_estimate_of_times = current_estimate

    def time_since_last_called(self) -> float:
        time_of_last_call = self.get_and_set_time_of_last_call()
        current_time = self.current_time

        return current_time - time_of_last_call

    def get_and_set_time_of_last_call(self):
        time_of_last_iter = copy(getattr(self, "_time_of_last_call", self.start_time))
        self._time_of_last_call = self.current_time

        return time_of_last_iter

    def elapsed_time(self):
        return self.current_time - self.start_time

    @property
    def start_time(self):
        return self._start_time

    @property
    def current_time(self):
        return time.time()

    def iterate(self):
        self.current_iter += 1
        self.update_time_estimate()
        if self.number_of_blocks_changed() or self._show_each_time:
            self.display_bar()

        if self.current_iter == self.range_to_iter:
            self.finished()

    def how_many_blocks_had(self):
        return int(self.current_iter / self.range_per_block)

    def how_many_blocks_left(self):
        return int((self.range_to_iter - self.current_iter) / self.range_per_block)

    def number_of_blocks_changed(self):
        original_blocks = self._how_many_blocks_displayed
        new_blocks = self.how_many_blocks_had()

        if new_blocks > original_blocks:
            return True
        else:
            return False

    def display_bar(self):
        percents = round(100.0 * self.current_iter / float(self.range_to_iter), 1)
        if self._show_timings:
            time_remaining = self.estimated_time_remaining()
            time_elapsed = self.elapsed_time()
            total_est_time = time_elapsed + time_remaining
            time_str = "(%.1f/%.1f/%.1f secs left/elapsed/total)" % (
                time_remaining,
                time_elapsed,
                total_est_time,
            )
        else:
            time_str = ""

        bar = "=" * self.how_many_blocks_had() + "-" * self.how_many_blocks_left()
        progress_string = "\0\r [%s] %s%s %s %s" % (
            bar,
            percents,
            "%",
            self.suffix,
            time_str,
        )
        sys.stdout.write(progress_string)
        sys.stdout.flush()
        self._how_many_blocks_displayed = self.how_many_blocks_had()

    def finished(self):
        self.display_bar()
        sys.stdout.write("\n")


def override_tuple_fields(original_tuple_instance, dict_of_new_fields: dict):
    original_tuple_instance_as_dict = named_tuple_as_dict(original_tuple_instance)
    combined_dict = dict(original_tuple_instance_as_dict, **dict_of_new_fields)
    original_tuple_class = original_tuple_instance.__class__
    try:
        new_named_tuple = original_tuple_class(**combined_dict)
    except:
        raise Exception(
            "One or more of new fields %s don't belong in named tuple %s"
            % (str(dict_of_new_fields), str(original_tuple_instance))
        )
    return new_named_tuple


def named_tuple_as_dict(original_tuple_instance) -> dict:
    return dict(
        [
            (field_name, getattr(original_tuple_instance, field_name))
            for field_name in original_tuple_instance._fields
        ]
    )
