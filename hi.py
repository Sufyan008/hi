#!/usr/bin/env bash
# indent type=tab
# tab size=4
# shellcheck disable=SC2034 #Unused variables
# shellcheck disable=SC2068 #Double quote array warning
# shellcheck disable=SC2086 # Double quote warning
## shellcheck disable=SC2120
# shellcheck disable=SC2162 #Read without -r
# shellcheck disable=SC2206 #Word split warning
# shellcheck disable=SC2178 #Array to string warning
# shellcheck disable=SC2102 #Ranges only match single
# shellcheck disable=SC2004 #arithmetic brackets warning
# shellcheck disable=SC2017 #arithmetic precision warning
# shellcheck disable=SC2207 #split array warning


# Copyright 2020 Aristocratos

#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at

#        http://www.apache.org/licenses/LICENSE-2.0

#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

declare -x LC_MESSAGES="C" LC_NUMERIC="C" LC_ALL=""

#* Fail if running on unsupported OS
case "$(uname -s)" in
	Linux*)  system=Linux;;
	Darwin*) system=MacOS;;
	CYGWIN*) system=Cygwin;;
	MINGW*)  system=MinGw;;
	*)       system="Other"
esac
if [[ "$system" != "Linux" ]]; then
	echo "This version of bashtop does not support $system platform."
	exit 1
fi

#* Fail if Bash version is below 4.4
bash_version_major="$(echo $BASH_VERSION | cut -d "." -f 1)"
bash_version_minor="$(echo $BASH_VERSION | cut -d "." -f 2)"
if [[ "$bash_version_major" -lt 4 ]] || [[ "$bash_version_major" == 4 && "$bash_version_minor" -lt 4 ]]; then
	echo "ERROR: Bash 4.4 or later is required (you are using Bash $bash_version_major.$bash_version_minor)."
	echo "       Consider upgrading your distribution to get a more recent Bash version."
	exit 1
fi

shopt -qu failglob nullglob
shopt -qs extglob globasciiranges globstar

declare -a banner banner_colors

banner=(
"██████╗  █████╗ ███████╗██╗  ██╗████████╗ ██████╗ ██████╗ "
"██╔══██╗██╔══██╗██╔════╝██║  ██║╚══██╔══╝██╔═══██╗██╔══██╗"
"██████╔╝███████║███████╗███████║   ██║   ██║   ██║██████╔╝"
"██╔══██╗██╔══██║╚════██║██╔══██║   ██║   ██║   ██║██╔═══╝ "
"██████╔╝██║  ██║███████║██║  ██║   ██║   ╚██████╔╝██║     "
"╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝     ")
declare version="0.8.16"
declare banner_width=${#banner[0]}
banner_colors=("#E62525" "#CD2121" "#B31D1D" "#9A1919" "#801414")

#? Start default variables------------------------------------------------------------------------------>
#? These values are used to create "$HOME/.config/bashtop/bashtop.cfg"
#? Any changes made here will be ignored if config file exists
aaa_config() { : ; } #! Do not remove this line!

#* Color theme, looks for a .theme file in "$HOME/.config/bashtop/themes", "Default" for builtin default theme
color_theme="Default"

#* Update time in milliseconds, increases automatically if set below internal loops processing time, recommended 2000 ms or above for better sample times for graphs
update_ms="2500"

#* Processes sorting, "pid" "program" "arguments" "threads" "user" "memory" "cpu lazy" "cpu responsive"
#* "cpu lazy" updates sorting over time, "cpu responsive" updates sorting directly at a cpu usage cost
proc_sorting="cpu lazy"

#* Reverse sorting order, "true" or "false"
proc_reversed="false"

#* Check cpu temperature, only works if "sensors" command is available and have values for "Package" and "Core"
check_temp="true"

#* Draw a clock at top of screen, formatting according to strftime, empty string to disable
draw_clock="%X"

#* Update main ui when menus are showing, set this to false if the menus is flickering too much for comfort
background_update="true"

#* Custom cpu model name, empty string to disable
custom_cpu_name=""

#* Enable error logging to "$HOME/.config/bashtop/error.log", "true" or "false"
error_logging="true"

aaz_config() { : ; } #! Do not remove this line!
#? End default variables-------------------------------------------------------------------------------->

declare -a menu_options menu_help menu_quit

menu_options=(
"┌─┐┌─┐┌┬┐┬┌─┐┌┐┌┌─┐"
"│ │├─┘ │ ││ ││││└─┐"
"└─┘┴   ┴ ┴└─┘┘└┘└─┘")
menu_help=(
"┬ ┬┌─┐┬  ┌─┐"
"├─┤├┤ │  ├─┘"
"┴ ┴└─┘┴─┘┴  ")
menu_quit=(
"┌─┐ ┬ ┬ ┬┌┬┐"
"│─┼┐│ │ │ │ "
"└─┘└└─┘ ┴ ┴ ")

menu_options_selected=(
"╔═╗╔═╗╔╦╗╦╔═╗╔╗╔╔═╗"
"║ ║╠═╝ ║ ║║ ║║║║╚═╗"
"╚═╝╩   ╩ ╩╚═╝╝╚╝╚═╝")
menu_help_selected=(
"╦ ╦╔═╗╦  ╔═╗"
"╠═╣║╣ ║  ╠═╝"
"╩ ╩╚═╝╩═╝╩  ")
menu_quit_selected=(
"╔═╗ ╦ ╦ ╦╔╦╗ "
"║═╬╗║ ║ ║ ║  "
"╚═╝╚╚═╝ ╩ ╩  ")

declare -A cpu mem swap proc net box theme
declare -a cpu_usage cpu_graph_a cpu_graph_b color_meter color_temp_graph color_cpu color_cpu_graph cpu_history color_mem_graph color_swap_graph
declare -a mem_history swap_history net_history_download net_history_upload mem_graph swap_graph proc_array download_graph upload_graph trace_array
declare resized=1 size_error clock tty_width tty_height hex="16#" cpu_p_box swap_on=1 draw_out esc_character boxes_out last_screen clock_out update_string
declare -a options_array=("color_theme" "update_ms" "proc_sorting" "check_temp" "draw_clock" "background_update" "error_logging" "custom_cpu_name")
declare -a save_array=("${options_array[@]}" "proc_reversed")
declare -a sorting=( "pid" "program" "arguments" "threads" "user" "memory" "cpu lazy" "cpu responsive" )
declare -a pid_history detail_graph detail_history detail_mem_history
declare time_left timestamp_start timestamp_end timestamp_input_start timestamp_input_end time_string mem_out proc_misc prev_screen pause_screen filter input_to_filter
declare no_epoch proc_det proc_misc2 sleeping=0 detail_mem_graph proc_det2 proc_out curled git_version
declare esc_character tab backspace sleepy late_update skip_process_draw winches quitting theme_int
declare -a disks_free disks_total disks_name disks_free_percent saved_key themes
printf -v esc_character "\u1b"
printf -v tab "\u09"
printf -v backspace "\u7F"
printf -v enter_key "\uA"

read tty_height tty_width < <(stty size)

#* Symbols for graphs
declare -a graph_symbol
graph_symbol=(" " "⡀" "⣀" "⣄" "⣤" "⣦" "⣴" "⣶" "⣷" "⣾" "⣿")
graph_symbol+=( " " "⣿" "⢿" "⡿" "⠿" "⠻" "⠟"  "⠛" "⠙" "⠉" "⠈")
box[boxes]="cpu mem net processes"

cpu[threads]=0

#* Symbols for subscript function
subscript=("₀" "₁" "₂" "₃" "₄" "₅" "₆" "₇" "₈" "₉")

#* Symbols for create_box function
box[single_hor_line]="─"
box[single_vert_line]="│"
box[single_left_corner_up]="┌"
box[single_right_corner_up]="┐"
box[single_left_corner_down]="└"
box[single_right_corner_down]="┘"
box[single_title_left]="├"
box[single_title_right]="┤"

box[double_hor_line]="═"
box[double_vert_line]="║"
box[double_left_corner_up]="╔"
box[double_right_corner_up]="╗"
box[double_left_corner_down]="╚"
box[double_right_corner_down]="╝"
box[double_title_left]="╟"
box[double_title_right]="╢"

#* If using bash version 5, set timestamps with EPOCHREALTIME variable
if [[ -n $EPOCHREALTIME ]]; then
	get_ms() { #? Set given variable to current epoch millisecond with EPOCHREALTIME varialble
		local -n ms_out=$1
		ms_out=$((${EPOCHREALTIME/[.,]/}/1000))
	}

#* If not, use date command
else
	get_ms() { #? Set given variable to current epoch millisecond with date command
		local -n ms_out=$1
		read ms_out < <(date +%s%3N)
	}
fi

init_() { #? Collect needed information and set options before startig main loop
	local i
	#* Set terminal options, save and clear screen
	tput smcup
	stty -echo
	tput civis

	#* Check if "sensors" command is available, if not, disable temperature collection
	if [[ $check_temp != false ]] && command -v sensors >/dev/null 2>&1; then check_temp="true"; else check_temp="false"; fi

	#* Check if "curl" command is available, if not, disable update check and theme downloads
	if command -v curl >/dev/null 2>&1; then curled=1; else unset curled; fi

	#* Get number of cores and cpu threads
	get_cpu_info

	#* Get processor BCLK
	local param_var
	if [[ -e /usr/include/asm-generic/param.h ]]; then
		param_var="$(</usr/include/asm-generic/param.h)"
		get_value -v 'cpu[hz]' -sv "param_var" -k "define HZ" -i
	else 
		cpu[hz]="100"
	fi

	#* Get max pid value and length
	proc[pid_max]="$(</proc/sys/kernel/pid_max)"
	proc[pid_len]=${#proc[pid_max]}
	if [[ ${proc[pid_len]} -lt 5 ]]; then proc[pid_len]=5; fi

	#* Call init for cpu data collection
	collect_cpu init

	#* Call init for memory data collection and check if swap is available
	mem[counter]=10
	collect_mem init

	#* Get default network device from "ip route" command and call init for net collection
	get_value -v 'net[device]' -ss "$(ip route get 1.1.1.1)" -k "dev" -mk 1
	collect_net init

	#* Check if newer version of bashtop is available from https://github.com/aristocratos/bashtop
	if [[ -n $curled ]]; then
		if ! get_value -v git_version -ss "$(curl -m 2 --raw -r 0-3500 https://raw.githubusercontent.com/aristocratos/bashtop/master/bashtop 2>/dev/null)" -k "version=" -r "[^0-9.]"; then unset git_version; fi
	fi

	#* Draw banner to banner array
	local letter b_color banner_line y=0
	local -a banner_out
	#print -v banner_out[0] -t "\e[0m"
	for banner_line in "${banner[@]}"; do
		#* Read banner array letter by letter to set correct color for filled vs outline characters
		while read -rN1 letter; do 
			if [[ $letter == "█" ]]; then b_color="${banner_colors[$y]}"
			else b_color=$((80-y*6)); fi
			if [[ $letter == " " ]]; then
				print -v banner_out[y] -r 1
			else
				print -v banner_out[y] -fg ${b_color} "${letter}"
			fi
		done <<<"$banner_line"
		((++y))
	done
	print -v banner_out[y] -rs -fg cc -b "← esc"
	if [[ -n $git_version && $git_version != "$version" ]]; then print -v banner_out[y] -rs -fg "#80cc80" -r 15 "[${git_version} available!]" -r $((9-${#git_version}))
	else print -v banner_out[y] -r 37; fi
	print -v banner_out[y] -fg cc -i -b "Version: ${version}" -rs
	unset 'banner[@]'
	banner=("${banner_out[@]}")

	#* Get theme and set colors
	color_init_

	#* Set up internals for quick processes sorting switching
	for((i=0;i<${#sorting[@]};i++)); do
		if [[ ${sorting[i]} == "${proc_sorting}" ]]; then
			proc[sorting_int]=$i
			break
		fi
	done
	if [[ -z ${proc[sorting_int]} ]]; then
		proc[sorting_int]=0
		proc_sorting="${sorting[0]}"
	fi

	if [[ ${proc_reversed} == true ]]; then
		proc[reverse]="+"
	else
		unset 'proc[reverse]'
	fi

	#* Wait for resize if terminal size is smaller then 80x25
	if (($tty_width<80 | $tty_height<25)); then resized; fi
	
	#* Calculate sizes of boxes
	calc_sizes
	

	#* Call init for processes data collection
	proc[selected]=0
	proc[page]=1
	collect_processes init
	
}

color_init_() { #? Check for theme file and set colors
	local main_bg="" main_fg="#cc" title="#ee" hi_fg="#90" inactive_fg="#40" cpu_box="#3d7b46" mem_box="#8a882e" net_box="#423ba5" proc_box="#923535" proc_misc="#0de756" selected_bg="#7e2626" selected_fg="#ee"
	local temp_start="#4897d4" temp_mid="#5474e8" temp_end="#ff40b6" cpu_start="#50f095" cpu_mid="#f2e266" cpu_end="#fa1e1e" div_line="#30"
	local free_start="#223014" free_mid="#b5e685" free_end="#dcff85" cached_start="#0b1a29" cached_mid="#74e6fc" cached_end="#26c5ff" available_start="#292107" available_mid="#ffd77a" available_end="#ffb814"
	local used_start="#3b1f1c" used_mid="#d9626d" used_end="#ff4769" download_start="#231a63" download_mid="#4f43a3" download_end="#b0a9de" upload_start="#510554" upload_mid="#7d4180" upload_end="#dcafde"
	local hex2rgb color_name array_name this_color main_fg_dec sourced theme_unset
	local -i i y
	local -A rgb
	local -a dec_test
	local -a convert_color=("main_bg" "temp_start" "temp_mid" "temp_end" "cpu_start" "cpu_mid" "cpu_end" "upload_start" "upload_mid" "upload_end" "download_start" "download_mid" "download_end" "used_start" "used_mid" "used_end" "available_start" "available_mid" "available_end" "cached_start" "cached_mid" "cached_end" "free_start" "free_mid" "free_end" "proc_misc" "main_fg_dec")
	
	for theme_unset in ${!theme[@]}; do
		unset 'theme[${theme_unset}]'
	done
	
	#* Check if theme set in config exists and source it if it does
	if [[ -n ${color_theme} && ${color_theme} != "Default" && -e "${theme_dir}/${color_theme%.theme}.theme" ]]; then
		# shellcheck source=/dev/null
		source "${theme_dir}/${color_theme%.theme}.theme"
		sourced=1
	else
		color_theme="Default"
	fi

	main_fg_dec="${theme[main_fg]:-$main_fg}"
	theme[main_fg_dec]="${main_fg_dec}"

	#* Convert colors for graphs and meters from rgb hexadecimal to rgb decimal if needed
	for color_name in ${convert_color[@]}; do
		if [[ -n $sourced ]]; then hex2rgb="${theme[${color_name}]}"
		else hex2rgb="${!color_name}"; fi
	 	
		hex2rgb=${hex2rgb//#/}

	 	if [[ ${#hex2rgb} == 6 ]] && is_hex "$hex2rgb"; then hex2rgb="$((${hex}${hex2rgb:0:2})) $((${hex}${hex2rgb:2:2})) $((${hex}${hex2rgb:4:2}))"
	 	elif [[ ${#hex2rgb} == 2 ]] && is_hex "$hex2rgb"; then hex2rgb="$((${hex}${hex2rgb:0:2})) $((${hex}${hex2rgb:0:2})) $((${hex}${hex2rgb:0:2}))"
		else 
			dec_test=(${hex2rgb})
			if [[ ${#dec_test[@]} -eq 3 ]] && is_int "${dec_test[@]}"; then hex2rgb="${dec_test[*]}"
			else unset hex2rgb; fi
		fi

		theme[${color_name}]="${hex2rgb}"
	done

	#* Set background color if set, otherwise use terminal default
	if [[ -n ${theme[main_bg]} ]]; then theme[main_bg_dec]="${theme[main_bg]}"; theme[main_bg]=";48;2;${theme[main_bg]// /;}"; fi
	
	#* Set colors from theme file if found, otherwise use default values
	theme[main_fg]="${theme[main_fg]:-$main_fg}"
	theme[title]="${theme[title]:-$title}"
	theme[hi_fg]="${theme[hi_fg]:-$hi_fg}"
	theme[div_line]="${theme[div_line]:-$div_line}"
	theme[inactive_fg]="${theme[inactive_fg]:-$inactive_fg}"
	theme[selected_fg]="${theme[selected_fg]:-$selected_fg}"
	theme[selected_bg]="${theme[selected_bg]:-$selected_bg}"
	box[cpu_color]="${theme[cpu_box]:-$cpu_box}"
	box[mem_color]="${theme[mem_box]:-$mem_box}"
	box[net_color]="${theme[net_box]:-$net_box}"
	box[processes_color]="${theme[proc_box]:-$proc_box}"
	
	#* Create color arrays from one, two or three color gradient, 100 values in each
	for array_name in "temp" "cpu" "upload" "download" "used" "available" "cached" "free"; do
		local -n color_array="color_${array_name}_graph"
		local -a rgb_start=(${theme[${array_name}_start]}) rgb_mid=(${theme[${array_name}_mid]}) rgb_end=(${theme[${array_name}_end]})
		local pf_calc middle=1
		
		rgb[red]=${rgb_start[0]}; rgb[green]=${rgb_start[1]}; rgb[blue]=${rgb_start[2]}

		if [[ -z ${rgb_mid[*]} ]] && ((rgb_end[0]+rgb_end[1]+rgb_end[2]>rgb_start[0]+rgb_start[1]+rgb_start[2])); then 
			rgb_mid=( $((rgb_end[0]/2)) $((rgb_end[1]/2)) $((rgb_end[2]/2)) )
		elif [[ -z ${rgb_mid[*]} ]]; then
			rgb_mid=( $((rgb_start[0]/2)) $((rgb_start[1]/2)) $((rgb_start[2]/2)) )
		fi
		
		for((i=0;i<=100;i++,y=0)); do	

			if [[ -n ${rgb_end[*]} ]]; then
				for this_color in "red" "green" "blue"; do
					if ((i==50)); then rgb_start[y]=${rgb[$this_color]}; fi
					
					if ((middle==1 & rgb[$this_color]<rgb_mid[y])); then
						printf -v pf_calc "%.0f" "$(( i*( (rgb_mid[y]-rgb_start[y])*100/50*100) ))e-4"

					elif ((middle==1 & rgb[$this_color]>rgb_mid[y])); then
						printf -v pf_calc "%.0f" "-$(( i*( (rgb_start[y]-rgb_mid[y])*100/50*100) ))e-4"

					elif ((middle==0 & rgb[$this_color]<rgb_end[y])); then
						printf -v pf_calc "%.0f" "$(( (i-50)*( (rgb_end[y]-rgb_start[y])*100/50*100) ))e-4"

					elif ((middle==0 & rgb[$this_color]>rgb_end[y])); then
						printf -v pf_calc "%.0f" "-$(( (i-50)*( (rgb_start[y]-rgb_end[y])*100/50*100) ))e-4"

					else
						pf_calc=0
					fi
					
					rgb[$this_color]=$((rgb_start[y]+pf_calc))
					if ((rgb[$this_color]<0)); then rgb[$this_color]=0
					elif ((rgb[$this_color]>255)); then rgb[$this_color]=255; fi
					
					y+=1
					if ((i==49 & y==3 & middle==1)); then middle=0; fi
				done
			fi
			color_array[i]="${rgb[red]} ${rgb[green]} ${rgb[blue]}"
		done

	done
}

quit_() { #? Clean exit
	#* Restore terminal options and screen
	tput rmcup
	stty echo
	tput cnorm

	#* Save any changed values to config file
	if [[ $config_file != "/dev/null" ]]; then
		save_config "${save_array[@]}"
	fi
	
	exit 0
}

sleep_() { #? Restore terminal options, stop and send to background if caught SIGTSTP (ctrl+z)
	tput rmcup
	stty echo
	tput cnorm
	
	kill -s SIGSTOP $$
}

resume_() { #? Set terminal options and resume if caught SIGCONT ('fg' from terminal)
	sleepy=0
	tput smcup
	stty -echo
	tput civis

	if [[ -n $pause_screen ]]; then
		echo -en "$pause_screen"
	else
		echo -en "${boxes_out}${proc_det}${last_screen}${mem_out}${proc_misc}${proc_misc2}${update_string}${clock_out}"
	fi
}

traperr() { #? Function for reporting error line numbers
	local match len trap_muted err="${BASH_LINENO[0]}"

	len=$((${#trace_array[@]}))
	if ((len-->=1)); then
		while ((len>=${#trace_array[@]}-2)); do		
			if [[ $err == "${trace_array[$((len--))]}" ]]; then ((++match)) ; fi
		done
		if ((match==2 & len != -2)); then return
		elif ((match>=1)); then trap_muted="(MUTED!)"
		fi
	fi
	if ((len>100)); then unset 'trace_array[@]'; fi
	trace_array+=("$err")
	echo "$(printf "%(%X)T") ERROR: On line $err $trap_muted" >> "${config_dir}/error.log"
	
}

resized() { #? Get new terminal size if terminal is resized
	resized=1
	unset winches
	while ((++winches<5)); do
		read tty_height tty_width < <(stty size)
		if (($tty_width<80 | $tty_height<25)); then 
			size_error_msg
			winches=0
		else
			create_box -w 30 -h 3 -c 1 -l 1 -lc "#EE2020" -title "resizing"
			print -jc 28 -fg ${theme[title]} "New size: ${tty_width}x${tty_height}"
			sleep 0.2
			if [[ $(stty size) != "$tty_height $tty_width" ]]; then winches=0; fi
		fi
	done
}

size_error_msg() { #? Shows error message if terminal size is below 80x25
	local width=$tty_width
	local height=$tty_height
	tput clear
	create_box -full -lc "#EE2020" -title "resize window"
	print -rs -m $((tty_height/2-1)) 2 -fg ${theme[title]} -c -l 11 "Current size: " -bg "#00" -fg dd2020 -d 1 -c "${tty_width}x${tty_height}" -rs
	print -d 1 -fg ${theme[title]} -c -l 15 "Need to be atleast:" -bg "#00" -fg 30dd50 -d 1 -c "80x25" -rs
	while [[ $(stty size) == "$tty_height $tty_width" ]]; do sleep 0.2; done
	
}

draw_banner() { #? Draw banner, usage: draw_banner <line> [output variable]
	local y letter b_color x_color xpos ypos=$1 banner_out
	if [[ -n $2 ]]; then local -n banner_out=$2; fi
	xpos=$(( (tty_width/2)-(banner_width/2) ))
	
	for banner_line in "${banner[@]}"; do
		print -v banner_out -rs -move $((ypos+++y)) $xpos -t "${banner_line}"
	done
	
	if [[ -z $2 ]]; then echo -en "${banner_out}"; fi
}

create_config() { #? Creates a new config file with default values from above
	local c_line c_read this_file
	this_file="$(realpath "$0")"
	echo "#? Config file for bashtop v. ${version}" > "$config_file"
	while IFS= read -r c_line; do
		if [[ $c_line =~ aaz_config() ]]; then break
		elif [[ $c_read == "1" ]]; then echo "$c_line" >> "$config_file"
		elif [[ $c_line =~ aaa_config() ]]; then c_read=1; fi
	done < "$this_file"
}

save_config() { #? Saves variables to config file if not same, usage: save_config "var1" ["var2"] ["var3"]...
	if [[ -z $1 || $config_file == "/dev/null" ]]; then return; fi
	local var tmp_conf tmp_value quote original new
	tmp_conf="$(<"$config_file")"
	for var in "$@"; do
		if [[ ${tmp_conf} =~ ${var} ]]; then
			get_value -v "tmp_value" -sv "tmp_conf" -k "${var}="
			if [[ ${tmp_value//\"/} != "${!var}" ]]; then
				original="${var}=${tmp_value}"
				new="${var}=\"${!var}\""
				sed -i "s/${original}/${new}/" "${config_file}"
			fi
		else
			echo "${var}=\"${!var}\"" >> "$config_file"
		fi
	done
}

set_font() { #? Take a string and generate a string of unicode characters of given font, usage; set_font "font-name [bold] [italic]" "string"
	local i letter letter_hex new_hex add_hex start font="$1" string_in="$2" string_out hex="16#"
	if [[ -z $font || -z $string_in ]]; then return; fi
	case "$font" in
		"sans-serif") lower_start="1D5BA"; upper_start="1D5A0"; digit_start="1D7E2";;
		"sans-serif bold") lower_start="1D5EE"; upper_start="1D5D4"; digit_start="1D7EC";;
		"sans-serif italic") lower_start="1D622"; upper_start="1D608"; digit_start="1D7E2";;
		#"sans-serif bold italic") start="1D656"; upper_start="1D63C"; digit_start="1D7EC";;
		"script") lower_start="1D4B6"; upper_start="1D49C"; digit_start="1D7E2";;
		"script bold") lower_start="1D4EA"; upper_start="1D4D0"; digit_start="1D7EC";;
		"fraktur") lower_start="1D51E"; upper_start="1D504"; digit_start="1D7E2";;
		"fraktur bold") lower_start="1D586"; upper_start="1D56C"; digit_start="1D7EC";;
		"monospace") lower_start="1D68A"; upper_start="1D670"; digit_start="1D7F6";;
		"double-struck") lower_start="1D552"; upper_start="1D538"; digit_start="1D7D8";;
		*) echo -n "${string_in}"; return;;
	esac

	for((i=0;i<${#string_in};i++)); do
		letter=${string_in:i:1}
		if [[ $letter =~ [a-z] ]]; then #61
			printf -v letter_hex '%X\n' "'$letter"
			printf -v add_hex '%X' "$((${hex}${letter_hex}-${hex}61))"
			printf -v new_hex '%X' "$((${hex}${lower_start}+${hex}${add_hex}))"
			string_out="${string_out}\U${new_hex}"
			#if [[ $font =~ sans-serif && $letter =~ m|w ]]; then string_out="${string_out} "; fi
			#\U205F
		elif [[ $letter =~ [A-Z] ]]; then #41
			printf -v letter_hex '%X\n' "'$letter"
			printf -v add_hex '%X' "$((${hex}${letter_hex}-${hex}41))"
			printf -v new_hex '%X' "$((${hex}${upper_start}+${hex}${add_hex}))"
			string_out="${string_out}\U${new_hex}"
			#if [[ $font =~ sans-serif && $letter =~ M|W ]]; then string_out="${string_out} "; fi
		elif [[ $letter =~ [0-9] ]]; then #30
			printf -v letter_hex '%X\n' "'$letter"
			printf -v add_hex '%X' "$((${hex}${letter_hex}-${hex}30))"
			printf -v new_hex '%X' "$((${hex}${digit_start}+${hex}${add_hex}))"
			string_out="${string_out}\U${new_hex}"
		else
			string_out="${string_out} \e[1D${letter}"
		fi
	done
	
	echo -en "${string_out}"
}

sort_array_int() {	#? Copy and sort an array of integers from largest to smallest value, usage: sort_array_int "input array" "output array"
	#* Return if given array has no values
	if [[ -z ${!1} ]]; then return; fi
	local start_n search_n tmp_array
	
	#* Create pointers to arrays
	local -n in_arr="$1"
	local -n out_arr="$2"

	#* Create local copy of array
	local array=("${in_arr[@]}")
	
	#* Start sorting
    for ((start_n=0;start_n<=${#array[@]}-1;++start_n)); do
        for ((search_n=start_n+1;search_n<=${#array[@]}-1;++search_n)); do
            if ((array[start_n]<array[search_n])); then
                tmp_array=${array[start_n]}
                array[start_n]=${array[search_n]}
                array[search_n]=$tmp_array
            fi
        done
    done
	
	#* Write the sorted array to output array
	out_arr=("${array[@]}")	
}

subscript() { #? Convert an integer to a string of subscript numbers
	local i out int=$1
	for((i=0;i<${#int};i++)); do
		out="${out}${subscript[${int:$i:1}]}"
	done
	echo -n "${out}"
}

spaces() { #? Prints back spaces, usage: spaces "number of spaces"
	printf "%${1}s" "" 
}

is_int() { #? Check if value(s) is integer
    local param
    for param; do
        if [[ ! $param =~ ^[\-]?[0-9]+$ ]]; then return 1; fi
    done
}

is_float() { #? Check if value(s) is floating point
    local param
    for param; do
        if [[ ! $param =~ ^[\-]?[0-9]*[,.][0-9]+$ ]]; then return 1; fi
    done
}

is_hex() { #? Check if value(s) is hexadecimal
    local param
    for param; do
        if [[ ! ${param//#/} =~ ^[0-9a-fA-F]*$ ]]; then return 1; fi
    done
}

floating_humanizer() { 	#? Convert integer to floating point and scale up in steps of 1024 to highest positive unit
						#? Usage: floating_humanizer <-b,-bit|-B,-Byte> [-ps,-per-second] [-s,-start "1024 multiplier start"] [-v,-variable-output] <input>
	local value selector per_second unit_mult decimals out_var ext_var
	local -a unit
	until (($#==0)); do
		case "$1" in
			-b|-bit) unit=(bit Kib Mib Gib Tib Pib); unit_mult=8;;
			-B|-Byte) unit=(Byte KiB MiB GiB TiB PiB); unit_mult=1;;
			-ps|-per-second) per_second=1;;
			-s|-start) selector="$2"; shift;;
			-v|-variable-output) local -n out_var="$2"; ext_var=1; shift;;
			*) if is_int "$1"; then value=$1; break; fi;;
		esac
		shift
	done
	
	if [[ -z $value || $value -lt 0 || -z $unit_mult ]]; then return; fi

	if ((per_second==1 & unit_mult==1)); then per_second="/s"
	elif ((per_second==1)); then per_second="ps"; fi

	if ((value>0)); then
		value=$((value*100*unit_mult))

		until ((${#value}<6)); do
			value=$((value>>10))
			((++selector))
		done

		if ((${#value}<5 & ${#value}>=2 & selector>0)); then
			decimals=$((5-${#value}))
			value="${value::-2}.${value:(-${decimals})}"
		elif ((${#value}>=2)); then
			value="${value::-2}"
		fi
	fi

	out_var="${value} ${unit[$selector]}${per_second}"
	if [[ -z $ext_var ]]; then echo -n "${out_var}"; fi
}

get_cpu_info() {
	local lscpu_var param_var
	lscpu_var="$(lscpu)"
	if [[ -z ${cpu[threads]} || -z ${cpu[cores]} ]]; then
		get_value -v 'cpu[threads]' -sv "lscpu_var" -k "CPU(s):" -i
		get_value -v 'cpu[cores]' -sv "lscpu_var" -k "Core(s)" -i
	fi
	if [[ -z $custom_cpu_name ]]; then
		if ! get_value -v 'cpu[model]' -sv "lscpu_var" -k "Model name:" -a -b -k "CPU" -mk -1; then
			get_value -v 'cpu[model]' -sv "lscpu_var" -k "Model name:" -r "  "
		fi
	else
		cpu[model]="${custom_cpu_name}"
	fi
}

get_value() { #? Get a value from a file, variable or array by searching for a non spaced "key name" on the same line
	local match line_pos=1 int reg key all tmp_array input found input_line line_array line_val ext_var line_nr current_line match_key math removing ext_arr
	local -a remove
	until (($#==0)); do
		until (($#==0)); do
			case "$1" in
				-k|-key) key="$2"; shift;;														#? Key "string" on the same line as target value
				-m|-match) match="$2"; shift;;													#? If multiple matches on a line, match occurrence "x"
				-mk|-match-key) match_key=$2; line_pos=0; shift;;								#? Match in relation to key position, -1 for previous value, 1 for next value
				-b|-break) shift; break;;														#? Break up arguments for multiple searches
				-a|-all) all=1;;																#? Prints back found line including key
				-l|-line) line_nr="$2"; shift;;													#? Set target line if no key is available
				-ss|-source-string) input="$2"; shift;;											#? Argument string as source
				-sf|-source-file) input="$(<"$2")"; shift;;  									#? File as source
				-sv|-source-var) input="${!2}"; shift;;											#? Variable as source
				-sa|-source-array) local -n tmp_array=$2; input="${tmp_array[*]}"; shift;;		#? Array as source
				-fp|-floating-point) reg="[\-]?[0-9]*[.,][0-9]+"; match=1;;						#? Match floating point value
				-math) math="$2"; shift;;														#? Perform math on a integer value, "x" represents value, only works if "integer" argument is given
				-i|-integer) reg="[\-]?[0-9]+[.,]?[0-9]*"; int=1; match=1;;						#? Match integer value or float and convert to int
				-r|-remove) remove+=("$2"); shift;;												#? Format output by removing entered regex, can be used multiple times
				-v|-variable-out) local -n found="$2"; ext_var=1; shift;;						#? Output to variable
				-map|-map-array) local -n array_out="$2"; ext_var=1; ext_arr=1; shift;;			#? Map output to array
			esac
			shift
		done

		if [[ -z $input ]]; then return 1; fi
		if [[ -z $line_nr && -z $key ]]; then line_nr=1; fi

		while IFS='' read -r input_line; do
			((++current_line))
			if [[ -n $line_nr && $current_line -eq $line_nr || -z $line_nr && -n $key && ${input_line/${key}/} != "$input_line" ]]; then
				if [[ -n $all ]]; then 
					found="${input_line}"
					break

				elif [[ -z $match && -z $match_key && -z $reg ]]; then
					found="${input_line/${key}/}"
					break

				else 
					line_array=(${input_line/${key}/${key// /}})

				fi

				for line_val in "${line_array[@]}"; do
					if [[ -n $match_key && $line_val == "${key// /}" ]]; then
						if ((match_key<0 & line_pos+match_key>=0)) || ((match_key>=0 & line_pos+match_key<${#line_array[@]})); then
							found="${line_array[$((line_pos+match_key))]}"
							break 2
						else 
							return 1
						fi

					elif [[ -n $match_key ]]; then
						((++line_pos))

					elif [[ -n $reg && $line_val =~ ^${reg}$ || -z $reg && -n $match ]]; then
						if ((line_pos==match)); then
							found=${line_val}
							break 2
						fi
						((++line_pos))
					fi
				done
			fi
		done <<<"${input}"

		if [[ -z $found ]]; then return 1; fi

		if [[ -n ${remove[*]} ]]; then
			for removing in "${remove[@]}"; do
				found="${found//${removing}/}"
			done
		fi

		if [[ -n $int && $found =~ [.,] ]]; then
			found="${found/,/.}"
			printf -v found "%.0f" "${found}"
		fi

		if [[ -n $math && -n $int ]]; then
			math="${math//x/$found}"
			found=$((${math}))
		fi

		if (($#>0)); then
			input="${found}"
			unset key match match_key all reg found int 'remove[@]' current_line
			line_pos=1
		fi

	done
	
	if [[ -z $ext_var ]]; then echo "${found}"; fi
	if [[ -n $ext_arr ]]; then array_out=(${found}); fi
}

get_themes() {
	local file
	theme_int=0
	themes=("Default")
	for file in "${theme_dir}"/*.theme; do
		file="${file##*/}"
		if [[ ${file} != "*.theme" ]]; then themes+=("${file%.theme}"); fi
		if [[ ${themes[-1]} == "${color_theme}" ]]; then theme_int=${#themes[@]}-1; fi
	done
}

cur_pos() { #? Get cursor postion, argument "line" prints current line, argument "col" prints current column, no argument prints both in format "line column"
    local line col 
    IFS=';' read -sdR -p $'\E[6n' line col
    if [[ -z $1 || $1 == "line" ]]; then echo -n "${line#*[}${1:-" "}"; fi
	if [[ -z $1 || $1 == "col" ]]; then echo -n "$col"; fi
}

create_box() { #? Draw a box with an optional title at given location
	local width height col line title ltype hpos vpos i hlines vlines color line_color c_rev=0 box_out ext_var fill
	until (($#==0)); do
		case $1 in
			-f|-full) col=1; line=1; width=$((tty_width)); height=$((tty_height));;							#? Use full terminal size for box 
			-c|-col) if is_int "$2"; then col=$2; shift; fi;; 												#? Column position to start box
			-l|-line) if is_int "$2"; then line=$2; shift; fi;; 											#? Line position to start box
			-w|-width) if is_int "$2"; then width=$2; shift; fi;; 											#? Width of box
			-h|-height) if is_int "$2"; then height=$2; shift; fi;; 										#? Height of box
			-t|-title) if [[ -n $2 ]]; then title="$2"; shift; fi;;											#? Draw title without titlebar
			-s|-single) ltype="single";;																	#? Use single lines
			-d|-double) ltype="double";;																	#? Use double lines
			-lc|-line-color) line_color="$2"; shift;;														#? Color of the lines
			-fill) fill=1;;																					#? Fill background of box
			-v|-variable) local -n box_out=$2; ext_var=1; shift;;											#? Output box to a variable
		esac
		shift
	done
	if [[ -z $col || -z $line || -z $width || -z $height ]]; then return; fi

	ltype=${ltype:-"single"}
	vlines+=("$col" "$((col+width-1))")
	hlines+=("$line" "$((line+height-1))")

	print -v box_out -rs

	#* Fill box if enabled
	if [[ -n $fill ]]; then
		for((i=line+1;i<line+height-1;i++)); do
			print -v box_out -m $i $((col+1)) -rp $((width-2)) -t " "
		done
	fi

	#* Draw all horizontal lines
	print -v box_out -fg ${line_color:-${theme[div_line]}}
	for hpos in "${hlines[@]}"; do
		print -v box_out -m $hpos $col -rp $((width-1)) -t "${box[${ltype}_hor_line]}"
	done

	#* Draw all vertical lines
	for vpos in "${vlines[@]}"; do
		print -v box_out -m $line $vpos
		for((hpos=line;hpos<=line+height-1;hpos++)); do
			print -v box_out -m $hpos $vpos -t "${box[${ltype}_vert_line]}"
		done
	done

	#* Draw corners
	print -v box_out -m $line $col -t "${box[${ltype}_left_corner_up]}"
	print -v box_out -m $line $((col+width-1)) -t "${box[${ltype}_right_corner_up]}"
	print -v box_out -m $((line+height-1)) $col -t "${box[${ltype}_left_corner_down]}"
	print -v box_out -m $((line+height-1)) $((col+width-1)) -t "${box[${ltype}_right_corner_down]}"

	#* Draw small title without titlebar
	if [[ -n $title ]]; then
		print -v box_out -m $line $((col+2)) -t "┤" -fg ${theme[title]} -b -t "$title" -rs -fg ${line_color:-${theme[div_line]}} -t "├"
	fi

	print -v box_out -rs -m $((line+1)) $((col+1))

	if [[ -z $ext_var ]]; then echo -en "${box_out}"; fi	
	
	
}

create_meter() { 	#? Create a horizontal percentage meter, usage; create_meter <value 0-100>
					#? Optional arguments: [-p, -place <line> <col>] [-w, -width <columns>] [-f, -fill-empty] 
					#? [-c, -color "array-name"] [-i, -invert-color] [-v, -variable "variable-name"]
	if [[ -z $1 ]]; then return; fi
	local val width colors color block="■" i fill_empty col line var ext_var out meter_var print_var invert bg_color=${theme[inactive_fg]}

	#* Argument parsing
	until (($#==0)); do
		case $1 in
			-p|-place) if is_int "${@:2:2}"; then line=$2; col=$3; shift 2; fi;;								#? Placement for meter
			-w|-width) width=$2; shift;;																		#? Width of meter in columns
			-c|-color) local -n colors=$2; shift;;																#? Name of an array containing colors from index 0-100
			-i|-invert) invert=1;;																				#? Invert meter
			-f|-fill-empty) fill_empty=1;;																		#? Fill unused space with dark blocks
			-v|-variable) local -n meter_var=$2; ext_var=1; shift;;												#? Output meter to a variable
			*) if is_int "$1"; then val=$1; fi;;
		esac
		shift
	done

	if [[ -z $val ]]; then return; fi

	#* Set default width if not given
	width=${width:-10}

	#* If no color array was given, create a simple greyscale array
	if [[ -z $colors ]]; then
		for ((i=0,ic=50;i<=100;i++,ic=ic+2)); do
			colors[i]="${ic} ${ic} ${ic}"
		done
	fi

	#* Create the meter
	meter_var=""
	if [[ -n $line && -n $col ]]; then print -v meter_var -rs -m $line $col
	else print -v meter_var -rs; fi

	if [[ -n $invert ]]; then print -v meter_var -r $((width+1)); fi
	for((i=1;i<=width;i++)); do
		if [[ -n $invert ]]; then print -v meter_var -l 2; fi

		if ((val>=i*100/width)); then 
			print -v meter_var -fg ${colors[$((i*100/width))]} -t "${block}"
		elif ((fill_empty==1)); then
			if [[ -n $invert ]]; then print -v meter_var -l $((width-i)); fi
			print -v meter_var -fg $bg_color -rp $((1+width-i)) -t "${block}"; break
		else
			if [[ -n $invert ]]; then break; print -v meter_var -l $((1+width-i))
			else print -v meter_var -r $((1+width-i)); break; fi
		fi
	done
	if [[ -z $ext_var ]]; then echo -en "${meter_var}"; fi	
}

create_graph() { 	#? Create a graph from an array of percentage values, usage; 	create_graph <options> <value-array>
					#? Create a graph from an array of non percentage values:       create_graph <options> <-max "max value"> <value-array>
					#? Add a value to existing graph; 								create_graph [-i, -invert] [-max "max value"] -add-value "graph_array" <value>
					#? Add last value from an array to existing graph; 				create_graph [-i, -invert] [-max "max value"] -add-last "graph_array" "value-array"
					#? Options: < -d, -dimensions <line> <col> <height> <width> > [-i, -invert] [-n, -no-guide] [-c, -color "array-name"] [-o, -output-array "variable-name"]
	if [[ -z $1 ]]; then return; fi
	local val col s_col line s_line height s_height width s_width colors color i var ext_var out side_num side_nums=1 add add_array invert no_guide max
	local -a graph_array input_array

	#* Argument parsing
	until (($#==0)); do
		case $1 in
			-d|-dimensions) if is_int "${@:2:4}"; then line=$2; col=$3; height=$4; width=$5; shift 4; fi;;						#? Graph dimensions
			-c|-color) local -n colors=$2; shift;;																				#? Name of an array containing colors from index 0-100
			-o|-output-array) local -n output_array=$2; ext_var=1; shift;;														#? Output meter to an array				
			-add-value) if is_int "$3"; then local -n output_array=$2; add=$3; break; else return; fi;;							#? Add a value to existing graph
			-add-last) local -n output_array=$2; local -n add_array=$3; add=${add_array[-1]}; break;;							#? Add last value from array to existing graph
			-i|-invert) invert=1;;																								#? Invert graph, drawing from top to bottom
			-n|-no-guide) no_guide=1;;																							#? Don't print side and bottom guide lines
			-max) if is_int "$2"; then max=$2; shift; fi;;																		#? Needed max value for non percentage arrays
			*) local -n tmp_in_array=$1; input_array=("${tmp_in_array[@]}");;
		esac
		shift
	done

	if [[ -z $no_guide ]]; then 
		((--height))
	else
		if [[ -n $invert ]]; then ((line--)); fi
	fi


	if ((width<3)); then width=3; fi
	if ((height<1)); then height=1; fi


	#* If argument "add" was passed check for existing graph and make room for new value(s)
	local add_start add_end
	if [[ -n $add ]]; then
		local cut_left search
		if [[ -n ${input_array[0]} ]]; then return; fi
		if [[ -n $output_array ]]; then
			graph_array=("${output_array[@]}")
			if [[ -z ${graph_array[0]} ]]; then return; fi
		else 
			return
		fi
		height=$((${#graph_array[@]}-1))
		input_array[0]=${add}

		#* Remove last value in current graph

		for ((i=0;i<height;i++)); do
			cut_left="${graph_array[i]%m*}"
			search=$((${#cut_left}+1))
			graph_array[i]="${graph_array[i]::$search}${graph_array[i]:$((search+1))}"
		done

	fi

	#* Initialize graph if no "add" argument was given
	if [[ -z $add ]]; then
		#* Scale down graph one line if height is even
		local inv_offset h_inv normal_vals=1
		local -a side_num=(100 0) g_char=(" ⡇" " ⠓" "⠒") g_index

		if [[ -n $invert ]]; then
			for((i=height;i>=0;i--)); do
				g_index+=($i)
			done
			
		else
			for((i=0;i<=height;i++)); do
				g_index+=($i)
			done
		fi
			
		if [[ -n $no_guide ]]; then unset normal_vals
		elif [[ -n $invert ]]; then g_char=(" ⡇" " ⡤" "⠤")
		fi

		#* Set up graph array print side numbers and lines
		print -v graph_array[0] -rs 
		print -v graph_array[0] -m $((line+g_index[0])) ${col} ${normal_vals:+-jr 3 -fg ee -b -t "${side_num[0]}" -rs -fg ${theme[main_fg]} -t "${g_char[0]}"} -fg ${colors[100]}
		for((i=1;i<height;i++)); do
			print -v graph_array[i] -m $((line+g_index[i])) ${col} ${normal_vals:+-r 3 -fg ${theme[main_fg]} -t "${g_char[0]}"} -fg ${colors[$((100-i*100/height))]}
		done
		
		if [[ -z $no_guide ]]; then width=$((width-5)); fi
		
		graph_array[height]=""
		if [[ -z $no_guide ]]; then
			print -v graph_array[$height] -m $((line+g_index[(-1)])) ${col} -jr 3 -fg ee -b -t "${side_num[1]}" -rs -fg ${theme[main_fg]} -t "${g_char[1]}" -rp ${width} -t "${g_char[2]}"
		fi
		
		#* If no color array was given, create a simple greyscale array
		if [[ -z $colors ]]; then
			for ((i=0,ic=50;i<=100;i++,ic=ic+2)); do
				colors[i]="${ic} ${ic} ${ic}"
			done
		fi
	fi

	#* Create the graph
	local value_width x y a cur_value prev_value=100 symbol tmp_out compare found count virt_height=$((height*10))
	if [[ -n $add ]]; then
		value_width=1
	elif ((${#input_array[@]}<=width)); then 
		value_width=${#input_array[@]}; 
	else
		value_width=${width}
		input_array=("${input_array[@]:(-$width)}")
	fi
	
	if [[ -n $invert ]]; then
		y=$((height-1))
		done_val="-1"
	else
		y=0
		done_val=$height
	fi

	#* Convert input array to percentage values of max if a max value was given
	if [[ -n $max ]]; then
		for((i=0;i<${#input_array[@]};i++)); do
			if ((input_array[i]>=max)); then
				input_array[i]=100
			else
				input_array[i]=$((input_array[i]*100/max))
			fi		
		done
	fi
		
	until ((y==done_val)); do

		#* Print spaces to right-justify graph if number of values is less than graph width
		if [[ -z $add ]] && ((value_width<width)); then print -v graph_array[y] -rp $((width-value_width)) -t " "; fi
		
		cur_value=$(( virt_height-(y*10) ))
		next_value=$(( virt_height-((y+1)*10) ))

		count=0
		x=0

		#* Create graph by walking through all values for each line, speed up by counting similar values and print once, when difference is met
		while ((x<value_width)); do

			#* Print empty space if current value is less than percentage for current line
			while ((x<value_width & input_array[offset+x]*virt_height/100<next_value)); do
				((++count))
				((++x))
			done
			if ((count>0)); then
				print -v graph_array[y] -rp ${count} -t " "
				count=0
			fi

			#* Print current value in percent relative to graph size if current value is less than line percentage but greater than next line percentage
			while ((x<value_width & input_array[x]*virt_height/100<cur_value & input_array[x]*virt_height/100>=next_value)); do
				print -v graph_array[y] -t "${graph_symbol[${invert:+-}$(( (input_array[x]*virt_height/100)-next_value ))]}"
				((++x))
			done

			#* Print full block if current value is greater than percentage for current line
			while ((x<value_width & input_array[x]*virt_height/100==cur_value)) || ((x<value_width & input_array[x]*virt_height/100>cur_value)); do
				((++count))
				((++x))
			done
			if ((count>0)); then
				print -v graph_array[y] -rp ${count} -t "${graph_symbol[10]}"
				count=0
			fi
		done
	
	if [[ -n $invert ]]; then
		((y--)) || true
	else
		((++y))
	fi
	done
	
	#* Echo out graph if no argument for a output array was given
	if [[ -z $ext_var && -z $add ]]; then echo -en "${graph_array[*]}"
	else output_array=("${graph_array[@]}"); fi	
}

create_mini_graph() { 	#? Create a one line high graph from an array of percentage values, usage; 	create_mini_graph <options> <value-array>
						#? Add a value to existing graph; 						create_mini_graph [-i, -invert] [-nc, -no-color] [-c, -color "array-name"] -add-value "graph_variable" <value>
						#? Add last value from an array to existing graph; 		create_mini_graph [-i, -invert] [-nc, -no-color] [-c, -color "array-name"] -add-last "graph_variable" "value-array"
						#? Options: [-w, -width <width>] [-i, -invert] [-nc, -no-color] [-c, -color "array-name"] [-o, -output-variable "variable-name"]
	if [[ -z $1 ]]; then return; fi
	local val col s_col line s_line height s_height width s_width colors color i var ext_var out side_num side_nums=1 add invert no_guide graph_var no_color color_value

	#* Argument parsing
	until (($#==0)); do
		case $1 in
			-w|-width) if is_int "$2"; then width=$2; shift; fi;;									 						#? Graph width
			-c|-color) local -n colors=$2; shift;;																			#? Name of an array containing colors from index 0-100
			-nc|-no-color) no_color=1;;																						#? Set no color
			-o|-output-variable) local -n output_var=$2; ext_var=1; shift;;													#? Output graph to a variable
			-add-value) if is_int "$3"; then local -n output_var=$2; add=$3; break; else return; fi;;						#? Add a value to existing graph
			-add-last) local -n output_var=$2 add_array=$3; add="${add_array[-1]}"; break;; 								#? Add last value from array to existing graph
			-i|-invert) invert=1;;																							#? Invert graph, drawing from top to bottom
			*) local -n input_array=$1;;
		esac
		shift
	done

	if ((width<1)); then width=1; fi

	#* If argument "add" was passed check for existing graph and make room for new value(s)
	local add_start add_end
	if [[ -n $add ]]; then
		local cut_left search
		#if [[ -n ${input_array[0]} ]]; then return; fi
		if [[ -n $output_var ]]; then
			graph_var="${output_var}"
			if [[ -z ${graph_var} ]]; then return; fi
		else 
			return
		fi
		
		declare -a input_array
		input_array[0]=${add}

		#* Remove last value in current graph
		if [[ -n ${graph_var} && -z $no_color ]]; then
			if [[ ${graph_var::5} == "\e[1C" ]]; then
				graph_var="${graph_var#'\e[1C'}"
			else
				cut_left="${graph_var%%m*}"
				search=$((${#cut_left}+1))
				graph_var="${graph_var:$((search+1))}"
			fi
		elif [[ -n ${graph_var} && -n $no_color ]]; then
			if [[ ${graph_var::5} == "\e[1C" ]]; then
				#cut_left="${graph_var%%C*}"
				#search=$((${#cut_left}+1))
				#graph_var="${graph_var:$((search))}"
				graph_var="${graph_var#'\e[1C'}"
			else
				graph_var="${graph_var:1}"
			fi
		fi
	fi

	
	#* If no color array was given, create a simple greyscale array
	if [[ -z $colors && -z $no_color ]]; then
		for ((i=0,ic=50;i<=100;i++,ic=ic+2)); do
			colors[i]="${ic} ${ic} ${ic}"
		done
	fi
	

	#* Create the graph
	local value_width x=0 y a cur_value virt_height=$((height*10)) offset=0 org_value
	if [[ -n $add ]]; then
		value_width=1
	elif ((${#input_array[@]}<=width)); then 
		value_width=${#input_array[@]}; 
	else
		value_width=${width}
		offset=$((${#input_array[@]}-width))
	fi

	#* Print spaces to right-justify graph if number of values is less than graph width
		if [[ -z $add && -z $no_color ]] && ((value_width<width)); then print -v graph_var -rp $((width-value_width)) -t "\e[1C"	
		elif [[ -z $add && -n $no_color ]] && ((value_width<width)); then print -v graph_var -rp $((width-value_width)) -t "\e[1C"; fi		
		#* Create graph
		while ((x<value_width)); do
			#* Round current input_array value divided by 10 to closest whole number
			org_value=${input_array[offset+x]}
			if ((org_value<0)); then org_value=0; fi
			if ((org_value>=100)); then cur_value=10
			elif [[ ${#org_value} -gt 1 && ${org_value:(-1)} -ge 5 ]]; then cur_value=$((${org_value::1}+1))
			elif [[ ${#org_value} -gt 1 && ${org_value:(-1)} -lt 5 ]]; then cur_value=$((${org_value::1}))
			elif [[ ${org_value:(-1)} -ge 5 ]]; then cur_value=1
			else cur_value=0
			fi
			if [[ -z $no_color ]]; then
				color="-fg ${colors[$org_value]} "
			else
				color=""
			fi

			if [[ $cur_value == 0 ]]; then
				print -v graph_var -t "\e[1C"
			else
				print -v graph_var ${color}-t "${graph_symbol[${invert:+-}$cur_value]}"
			fi
			((++x))
		done	
	
	#* Echo out graph if no argument for a output array was given
	if [[ -z $ext_var && -z $add ]]; then echo -en "${graph_var}"
	else output_var="${graph_var}"; fi	
}

print() {	#? Print text, set true-color foreground/background color, add effects, center text, move cursor, save cursor position and restore cursor postion
			#? Effects: [-fg, -foreground <RGB Hex>|<R Dec> <G Dec> <B Dec>] [-bg, -background <RGB Hex>|<R Dec> <G Dec> <B Dec>] [-rs, -reset] [-/+b, -/+bold] [-/+da, -/+dark]
			#? [-/+ul, -/+underline] [-/+i, -/+italic] [-/+bl, -/+blink] [-f, -font "sans-serif|script|fraktur|monospace|double-struck"]
			#? Manipulation: [-m, -move <line> <column>] [-l, -left <x>] [-r, -right <x>] [-u, -up <x>] [-d, -down <x>] [-c, -center] [-sc, -save] [-rc, -restore]
			#? [-jl, -justify-left <width>] [-jr, -justify-right <width>] [-jc, -justify-center <width>] [-rp, -repeat <x>]
			#? Text: [-v, -variable "variable-name"] [-stdin] [-t, -text "string"] ["string"]
	
	#* Return if no arguments is given
	if [[ -z $1 ]]; then return; fi

	#* Just echo and return if only one argument and not a valid option
	if [[ $# -eq 1 && ${1::1} != "-"  ]]; then echo -en "$1"; return; fi
	
	local effect color add_command text text2 esc center clear fgc bgc fg_bg_div tmp tmp_len bold italic custom_font val var out ext_var hex="16#"
	local justify_left justify_right justify_center repeat r_tmp trans
	
	
	#* Loop function until we are out of arguments
	until (($#==0)); do

		#* Argument parsing
		until (($#==0)); do
			case $1 in
				-t|-text) if [[ -n $2 ]]; then text="$2"; shift 2; break; fi;;																#? String to print
				-stdin) text="$(</dev/stdin)"; shift; break;;																				#? Print from stdin
				-fg|-foreground)	#? Set text foreground color, accepts either 6 digit hexadecimal "#RRGGBB", 2 digit hex (greyscale) or decimal RGB "<0-255> <0-255> <0-255>"
					val=${2//#/}
					if is_int "${@:2:3}"; then fgc="\e[38;2;$2;$3;$4m"; shift 3
					elif [[ ${#val} == 6 ]] && is_hex "$val"; then fgc="\e[38;2;$((${hex}${val:0:2}));$((${hex}${val:2:2}));$((${hex}${val:4:2}))m"; shift
					elif [[ ${#val} == 2 ]] && is_hex "$val"; then fgc="\e[38;2;$((${hex}${val:0:2}));$((${hex}${val:0:2}));$((${hex}${val:0:2}))m"; shift
					fi
					;;										
				-bg|-background)	#? Set text background color, accepts either 6 digit hexadecimal "#RRGGBB", 2 digit hex (greyscale) or decimal RGB "<0-255> <0-255> <0-255>"
					val=${2//#/}
					if is_int "${@:2:3}"; then bgc="\e[48;2;$2;$3;$4m"; shift 3
					elif [[ ${#val} == 6 ]] && is_hex "$val"; then bgc="\e[48;2;$((${hex}${val:0:2}));$((${hex}${val:2:2}));$((${hex}${val:4:2}))m"; shift
					elif [[ ${#val} == 2 ]] && is_hex "$val"; then bgc="\e[48;2;$((${hex}${val:0:2}));$((${hex}${val:0:2}));$((${hex}${val:0:2}))m"; shift
					fi
					;;
				-c|-center) center=1;;																										#? Center text horizontally on screen
				-rs|-reset) effect="0${effect}${theme[main_bg]}";;																			#? Reset text colors and effects
				-b|-bold) effect="${effect}${effect:+;}1"; bold=1;;																			#? Enable bold text
				+b|+bold) effect="${effect}${effect:+;}21"; bold=0;;																		#? Disable bold text
				-da|-dark) effect="${effect}${effect:+;}2";;																				#? Enable dark text
				+da|+dark) effect="${effect}${effect:+;}22";;																				#? Disable dark text
				-i|-italic) effect="${effect}${effect:+;}3"; italic=1;;																		#? Enable italic text
				+i|+italic) effect="${effect}${effect:+;}23"; italic=0;;																	#? Disable italic text
				-ul|-underline) effect="${effect}${effect:+;}4";;																			#? Enable underlined text
				+ul|+underline) effect="${effect}${effect:+;}24";;																			#? Disable underlined text
				-bl|-blink) effect="${effect}${effect:+;}5";;																				#? Enable blinking text
				+bl|+blink) effect="${effect}${effect:+;}25";;																				#? Disable blinking text
				-f|-font) if [[ $2 =~ ^(sans-serif|script|fraktur|monospace|double-struck)$ ]]; then custom_font="$2"; shift; fi;;			#? Set custom font			
				-m|-move) if is_int "${@:2:2}"; then add_command="${add_command}\e[${2};${3}f"; shift 2; fi;;								#? Move to postion "LINE" "COLUMN"
				-l|-left) if is_int "$2"; then add_command="${add_command}\e[${2}D"; shift; fi;;											#? Move left x columns
				-r|-right) if is_int "$2"; then add_command="${add_command}\e[${2}C"; shift; fi;;											#? Move right x columns
				-u|-up) if is_int "$2"; then add_command="${add_command}\e[${2}A"; shift; fi;;												#? Move up x lines
				-d|-down) if is_int "$2"; then add_command="${add_command}\e[${2}B"; shift; fi;;											#? Move down x lines
				-jl|-justify-left) if is_int "$2"; then justify_left="${2}"; shift; fi;;													#? Justify string left within given width
				-jr|-justify-right) if is_int "$2"; then justify_right="${2}"; shift; fi;;													#? Justify string right within given width
				-jc|-justify-center) if is_int "$2"; then justify_center="${2}"; shift; fi;;												#? Justify string center within given width
				-rp|-repeat) if is_int "$2"; then repeat=${2}; shift; fi;;																	#? Repeat next string x number of times
				-sc|-save) add_command="\e[s${add_command}";;																				#? Save cursor position
				-rc|-restore) add_command="${add_command}\e[u";;																			#? Restore cursor position
				-trans) trans=1;;																											#? Make whitespace transparent
				-v|-variable) local -n var=$2; ext_var=1; shift;;																			#? Send output to a variable, appending if not unset	
				*) text="$1"; shift; break;;																								#? Assumes text string if no argument is found
			esac
			shift
		done

		#* Repeat string if repeat is enabled
		if [[ -n $repeat ]]; then
			printf -v r_tmp "%${repeat}s" ""
			text="${r_tmp// /$text}"
		fi

		#* Set correct placement for screen centered text
		if ((center==1 & ${#text}>0 & ${#text}<tty_width-4)); then
			add_command="${add_command}\e[${tty_width}D\e[$(( (tty_width/2)-(${#text}/2) ))C"
		fi

		#* Convert text string to custom font if set and remove non working effects
		if [[ -n $custom_font ]]; then
			unset effect
			text=$(set_font "${custom_font}${bold:+" bold"}${italic:+" italic"}" "${text}")
		fi

		#* Set text justification if set
		if [[ -n $justify_left ]] && ((${#text}<justify_left)); then
			printf -v text "%s%$((justify_left-${#text}))s" "${text}" ""
		elif [[ -n $justify_right ]] && ((${#text}<justify_right)); then
			printf -v text "%$((justify_right-${#text}))s%s" "" "${text}"
		elif [[ -n $justify_center ]] && ((${#text}<justify_center)); then
			printf -v text "%$(( (justify_center/2)-(${#text}/2) ))s%s" "" "${text}"
			printf -v text "%s%-$((justify_center-${#text}))s" "${text}" ""
		fi

		if [[ -n $trans ]]; then
			text="${text// /'\e[1C'}"
		fi

		#* Create text string
		if [[ -n $effect ]]; then effect="\e[${effect}m"; fi
		out="${out}${add_command}${effect}${bgc}${fgc}${text}"
		unset add_command effect fgc bgc center justify_left justify_right justify_center custom_font text repeat trans justify
	done

	#* Print the string to stdout if variable out hasn't been set
	if [[ -z $ext_var ]]; then echo -en "$out"
	else var="${var}${out}"; fi

}

collect_cpu() { #? Collects cpu stats from /proc/stat and compares with previously collected sample to get cpu usage
				#? Returns cpu usage in array "cpu_usage", index 0 is usage for all threads, following indices corresponds to thread usage in multicore/hyperthreading cpus
	local stat_array freq thread i threads=${cpu[threads]}

	#* Get values from /proc/stat, compare to get cpu usage
	thread=0
	while ((thread<threads+1)) && read -ra stat_array; do
		cpu[new_${thread}]=$((stat_array[1]+stat_array[2]+stat_array[3]+stat_array[4]))
		cpu[idle_new_${thread}]=${stat_array[4]}
		if [[ -n ${cpu[old_${thread}]} && -n ${cpu[idle_new_${thread}]} && ${cpu[old_${thread}]} -ne ${cpu[new_${thread}]} ]]; then 
			cpu_usage[${thread}]=$(( ( 100*(${cpu[old_${thread}]}-${cpu[new_${thread}]}-${cpu[idle_old_${thread}]}+${cpu[idle_new_${thread}]}) ) / (${cpu[old_${thread}]}-${cpu[new_${thread}]}) ))
		fi
		cpu[old_${thread}]=${cpu[new_${thread}]}
		cpu[idle_old_${thread}]=${cpu[idle_new_${thread}]}
		((++thread))
	done </proc/stat

	#* Copy cpu usage for cpu package and cores to cpu history arrays and trim earlier entries
	if ((${#cpu_history[@]}>tty_width*2)); then
		cpu_history=( "${cpu_history[@]:$tty_width}" "${cpu_usage[0]}")
	else
		cpu_history+=("${cpu_usage[0]}")
	fi

	for((i=1;i<=threads;i++)); do
		local -n cpu_core_history="cpu_core_history_$i"
		if ((${#cpu_core_history[@]}>20)); then
			cpu_core_history=( "${cpu_core_history[@]:10}" "${cpu_usage[$i]}")
		else
			cpu_core_history+=("${cpu_usage[$i]}")
		fi
	done
	
	#* Get current cpu frequency from "/proc/cpuinfo" and convert to appropriate unit
	if [[ -z ${cpu[no_cpu_info]} ]] && ! get_value -v 'cpu[freq]' -sf "/proc/cpuinfo" -k "cpu MHz" -i; then
		cpu[no_cpu_info]=1
	fi
	
	#* If getting cpu frequency from "proc/cpuinfo" was unsuccessfull try "/sys/devices/../../scaling_cur_freq"
	if [[ -n ${cpu[no_cpu_info]} && -e "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq" ]]; then
		get_value -v 'cpu[freq]' -sf "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq" -i
		printf -v 'cpu[freq]' "%.0f0" "${cpu[freq]}e-4"
	fi

	if ((${#cpu[freq]}>3)); then cpu[freq_string]="${cpu[freq]::-3}.${cpu[freq]:(-3):1} GHz"
	elif ((${#cpu[freq]}>1)); then cpu[freq_string]="${cpu[freq]} MHz"
	else cpu[freq_string]=""; fi

	#* Get load average and uptime from uptime command
	local uptime_var
	read -r uptime_var < <(uptime 2>/dev/null || true)
	cpu[load_avg]="${uptime_var#*average: }"
	cpu[load_avg]="${cpu[load_avg]//,/}"
	cpu[uptime]="${uptime_var#*up }"
	cpu[uptime]="${cpu[uptime]%%,  *}"

	#* Collect cpu temps if enabled
	if [[ $check_temp == true ]]; then collect_cpu_temps; fi
}

collect_cpu_temps() { #? Collect cpu temperatures
	local unit i it c div threads=${cpu[threads]} sens_var

	#* Fetch output from "sensors" command to a variable
	sens_var="$(sensors)"

	#* Get CPU package temp
	if get_value -v 'cpu[temp_0]' -sv "sens_var" -k "Package*:" -mk 1; then

		#* If successful get temperature unit, convert temp to integer and get high, crit and core temps
		cpu[temp_unit]=${cpu[temp_0]:(-2)}; cpu[temp_0]=${cpu[temp_0]%.*}; if [[ ${cpu[temp_0]::1} == "+" ]]; then cpu[temp_0]=${cpu[temp_0]#+}; fi
		if [[ -z ${cpu[temp_high]} ]]; then 
			get_value -v 'cpu[temp_high]' -sv "sens_var" -k "Package*high =" -m 2 -r "[^0-9.]" -b -i
			get_value -v 'cpu[temp_crit]' -sv "sens_var" -k "Package*crit =" -m 2 -r "[^0-9.]" -b -i
		fi
		for((i=0,it=1;i<threads;i++,it++)); do
			if ! get_value -v "cpu[temp_${it}]" -sv "sens_var" -k "Core ${i}:" -mk 1 -r "[^0-9.-]" -b -i; then break; fi
			#* If number of cores is less than number of threads copy current temp to "current core id"+"total cores"
			if ((cpu[cores]<cpu[threads])); then
				cpu[temp_$((it+cpu[cores]))]=${cpu[temp_${it}]}
			fi
		done

		for((i=0;i<=threads;i++)); do
			local -n cpu_temp_history="cpu_temp_history_$i"
			if ((${#cpu_temp_history[@]}>15)); then
				cpu_temp_history=( "${cpu_temp_history[@]:10}" "$(( (${cpu[temp_${i}]}-15)*100/(cpu[temp_high]-15) ))")
			else
				cpu_temp_history+=("$(( (${cpu[temp_${i}]}-15)*100/(cpu[temp_high]-15) ))")
			fi
		done
		

	#* If unsuccessful turn off temperature checking
	else
		check_temp="false"
	fi
}

collect_mem() { #? Collect memory information from "/proc/meminfo"
	((++mem[counter]))

	if ((mem[counter]<5)); then return; fi
	mem[counter]=0

	local i tmp value array mem_info
	local -a mem_array swap_array available=("mem")

	#* Get memory and swap information from "/proc/meminfo" and calculate percentages
	mem_info="$(</proc/meminfo)"
	
	get_value -v 'mem[total]' -sv "mem_info" -k "MemTotal:" -i
	get_value -v 'mem[available]' -sv "mem_info" -k "MemAvailable:" -i
	mem[available_percent]=$((mem[available]*100/mem[total]))
	
	mem[used]=$((mem[total]-mem[available]))
	mem[used_percent]=$((mem[used]*100/mem[total]))
	
	get_value -v 'mem[free]' -sv "mem_info" -k "MemFree:" -i
	mem[free_percent]=$((mem[free]*100/mem[total]))
	
	get_value -v 'mem[cached]' -sv "mem_info" -k "Cached:" -i
	mem[cached_percent]=$((mem[cached]*100/mem[total]))

	if [[ -n $swap_on ]] && get_value -v swap[total] -sv "mem_info" -k "SwapTotal:" -i && ((swap[total]>0)); then
		get_value -v 'swap[free]' -sv "mem_info" -k "SwapFree:" -i
		swap[free_percent]=$((swap[free]*100/swap[total]))
		
		swap[used]=$((swap[total]-swap[free]))
		swap[used_percent]=$((swap[used]*100/swap[total]))
		
		available+=("swap")
	else
		unset swap_on
	fi

	#* Convert values to floating point and humanize
	for array in ${available[@]}; do
		for value in total used free available cached; do
			if [[ $array == "swap" && $value == "available" ]]; then break 2; fi
			local -n this_value="${array}[${value}]" this_string="${array}[${value}_string]"
			floating_humanizer -v this_string -s 1 -B "${this_value}"
		done
	done

	#* Get disk information from "df" command
	local df_array df_line line_array
	unset 'disks_free[@]' 'disks_used[@]' 'disks_used_percent[@]' 'disks_total[@]' 'disks_name[@]' 'disks_free_percent[@]'
	readarray -t df_array < <(df -x squashfs -x tmpfs -x devtmpfs -x overlay)
	for df_line in "${df_array[@]:1}"; do
		line_array=(${df_line})

		if [[ ${line_array[5]} == "/" ]]; then disks_name+=("root")
		else disks_name+=("${line_array[5]##*/}"); fi
		disks_total+=("$(floating_humanizer -s 1 -B ${line_array[1]})")
		disks_used+=("$(floating_humanizer -s 1 -B ${line_array[2]})")
		disks_used_percent+=("${line_array[4]%'%'}")
		disks_free+=("$(floating_humanizer -s 1 -B ${line_array[3]})")
		disks_free_percent+=("$((100-${line_array[4]%'%'}))")

	done



}

collect_processes() { #? Collect process information and calculate accurate cpu usage
	local argument="$1"
	if [[ -n $skip_process_draw && $argument != "now" ]]; then return; fi
	local width=${box[processes_width]} height=${box[processes_height]} format_args format_cmd readline sort symbol="▼" cpu_title options pid_string tmp selected
	local -a grep_array

	if [[ $argument == "now" ]]; then skip_process_draw=1; fi

	if [[ -n ${proc[reverse]} ]]; then symbol="▲"; fi
	case ${proc_sorting} in
		"pid") selected="Pid:"; sort="pid";;
		"program") selected="Program:"; sort="comm";;
		"arguments") selected="Arguments:"; sort="args";;
		"threads") selected="Threads:"; sort="nlwp";;
		"user") selected="User:"; sort="euser";;
		"memory") selected="Mem%"; sort="pmem";;
		"cpu lazy"|"cpu responsive") sort="pcpu"; selected="Cpu%";;
	esac


	#* Collect output from ps command to array
	if ((width>60)); then format_args=",args:$(( width-(47+proc[pid_len]) ))=Arguments:"; format_cmd=15
	else format_cmd=$(( width-(31+proc[pid_len]) )); fi
	unset 'proc_array[@]' 'pid_array[@]'

	if ((proc[detailed]==0)) && [[ -n ${proc[detailed_name]} ]]; then
		unset 'proc[detailed_name]' 'proc[detailed_killed]' 'proc[detailed_cpu_int]' 'proc[detailed_cmd]'
		unset 'proc[detailed_mem]' 'proc[detailed_mem_int]' 'proc[detailed_user]' 'proc[detailed_threads]'
		unset 'detail_graph[@]' 'detail_mem_graph' 'detail_history[@]' 'detail_mem_history[@]'
		unset 'proc[detailed_runtime]' 'proc[detailed_mem_string]' 'proc[detailed_parent_pid]' 'proc[detailed_parent_name]'
	fi

	unset 'proc[detailed_cpu]'

	if [[ -z $filter ]]; then
	 	options="-t"
	fi

	readarray ${options} proc_array < <(ps ax -o pid:${proc[pid_len]}=Pid:,comm:${format_cmd}=Program:${format_args},nlwp:3=Tr:,euser:6=User:,pmem=Mem%,pcpu:10=Cpu% --sort ${proc[reverse]:--}${sort})
	
	proc_array[0]="${proc_array[0]/      Tr:/ Threads:}"
	proc_array[0]="${proc_array[0]/ ${selected}/${symbol}${selected}}"

	if [[ -n $filter ]]; then
		grep_array[0]="${proc_array[0]}"
	 	readarray -O 1 -t grep_array < <(echo -e " ${proc_array[*]:1}" | grep -e "${filter}" ${proc[detailed_pid]:+-e ${proc[detailed_pid]}} | cut -c 2- || true)
		proc_array=("${grep_array[@]}")
	fi

	proc[pages]=$(( (${#proc_array[@]}-1)/(height-3)+1 ))
	if ((proc[page]>proc[pages])); then proc[page]=${proc[pages]}; fi


	#* Get accurate cpu usage by fetching and comparing values in /proc/"pid"/stat
	local operations operation utime stime count time_elapsed cpu_percent_string rgb=231 step add proc_out tmp_value_array i pcpu_usage cpu_int tmp_percent breaking
	local -a cpu_percent statfile work_array

	#* Timestamp the values in milliseconds to accurately calculate cpu usage
	get_ms proc[new_timestamp]
	
	for readline in "${proc_array[@]:1}"; do
		 ((++count))

		if ((count==height-3)); then
			if [[ -n $filter || $proc_sorting == "cpu responsive" || ${proc[selected]} -gt 0 || ${proc[page]} -gt 1 || ${proc_reversed} == true ]]; then :
			else breaking=1; fi
		fi

		if get_key -save && [[ ${#saved_key[@]} -gt 0 ]]; then return; fi

		work_array=(${readline})

		pid="${work_array[0]}"
		pcpu_usage="${work_array[-1]}"


		if [[ ! ${pid_history[*]} =~ ${pid} ]]; then
			pid_history+=("${pid}")
		fi

		if [[ -n $filter || $proc_sorting == "cpu responsive" ]] && [[ ${proc_array[count]:${proc[pid_len]}:1} != " " ]]; then
			unset pid_string
			printf -v pid_string "%${proc[pid_len]}s" "${pid}"
			proc_array[count]="${pid_string}${proc_array[count]#*${pid}}"
		fi

		if [[ -r "/proc/${pid}/stat" ]] && read -ra statfile </proc/${pid}/stat 2>/dev/null; then

			utime=${statfile[13]}
			stime=${statfile[14]}
			
			proc[new_${pid}_ticks]=$((utime+stime))
		

			if [[ -n ${proc[old_${pid}_ticks]} ]]; then

				time_elapsed=$((proc[new_timestamp]-proc[old_timestamp]))
				
				#* Calculate current cpu usage for process, * 1000 (for conversion from ms to seconds) * 1000 (for conversion to floating point)
				cpu_percent[count]=$(( ( ( ${proc[new_${pid}_ticks]}-${proc[old_${pid}_ticks]} ) * 1000 * 1000 ) / ( cpu[hz]*time_elapsed*cpu[threads] ) ))

				if ((cpu_percent[count]<0)); then cpu_percent[count]=0
				elif ((cpu_percent[count]>1000)); then cpu_percent[count]=1000; fi
				
				if ((${#cpu_percent[count]}<=3)); then
					printf -v cpu_percent_string "%01d%s" "${cpu_percent[count]::-1}" ".${cpu_percent[count]:(-1)}"
				else
					cpu_percent_string=${cpu_percent[count]::-1}
				fi

				printf -v cpu_percent_string "%5s" "${cpu_percent_string::4}"

				proc_array[count]="${proc_array[count]::-5}${cpu_percent_string}"


				pid_graph="pid_${pid}_graph"
				local -n pid_count="pid_${pid}_count"

				printf -v cpu_int "%01d" "${cpu_percent[count]::-1}"

				#* Get info for detailed box if enabled
				if [[ ${pid} == "${proc[detailed_pid]}" ]]; then
					if [[ -z ${proc[detailed_name]} ]]; then
						local get_mem
						local -a det_array
						read -r proc[detailed_name] </proc/${pid}/comm ||true
						proc[detailed_cmd]="$(tr '\000' ' ' </proc/${pid}/cmdline)"						
						proc[detailed_name]="${proc[detailed_name]::15}"
						det_array=($(ps -o ppid:4,euser:15 --no-headers -p $pid || true))	
						proc[detailed_parent_pid]="${det_array[0]}"
						proc[detailed_user]="${det_array[*]:1}"
						proc[detailed_parent_name]="$(ps -o comm --no-headers -p ${det_array[0]} || true)"
						get_mem=1
					fi
					proc[detailed_cpu]="${cpu_percent_string// /}"
					proc[detailed_cpu_int]="${cpu_int}"
					proc[detailed_threads]="${work_array[-4]}"
					proc[detailed_runtime]="$(ps -o etime:4 --no-headers -p $pid || true)"

					if [[ ${proc[detailed_mem]} != "${work_array[-2]}" || -n $get_mem ]] || ((++proc[detailed_mem_count]>5)); then
						proc[detailed_mem_count]=0
						proc[detailed_mem]="${work_array[-2]}"
						proc[detailed_mem_int]="${proc[detailed_mem]/./}"
						if [[ ${proc[detailed_mem_int]::1} == "0" ]]; then proc[detailed_mem_int]="${proc[detailed_mem_int]:1}0"; fi
						#* Scale up low mem values to see any changes on mini graph
						if ((proc[detailed_mem_int]>900)); then proc[detailed_mem_int]=$((proc[detailed_mem_int]/10))
						elif ((proc[detailed_mem_int]>600)); then proc[detailed_mem_int]=$((proc[detailed_mem_int]/8))
						elif ((proc[detailed_mem_int]>300)); then proc[detailed_mem_int]=$((proc[detailed_mem_int]/5))
						elif ((proc[detailed_mem_int]>100)); then proc[detailed_mem_int]=$((proc[detailed_mem_int]/2))
						elif ((proc[detailed_mem_int]<50)); then proc[detailed_mem_int]=$((proc[detailed_mem_int]*2)); fi
						unset 'proc[detailed_mem_string]'
						floating_humanizer -v proc[detailed_mem_string] -B -s 1 "$(ps -o rss:1 --no-headers -p ${pid} || true)"
						if [[ -z ${proc[detailed_mem_string]} ]]; then proc[detailed_mem_string]="? Byte"; fi
					fi
					
					#* Copy process cpu usage to history array and trim earlier entries
					if ((${#detail_history[@]}>box[details_width]*2)); then
						detail_history=( "${detail_history[@]:${box[details_width]}}" "$((cpu_int+4))")
					else
						detail_history+=("$((cpu_int+4))")
					fi

					#* Copy process mem usage to history array and trim earlier entries
					if ((${#detail_mem_history[@]}>box[details_width])); then
						detail_mem_history=( "${detail_mem_history[@]:$((box[details_width]/2))}" "${proc[detailed_mem_int]}")
					else
						detail_mem_history+=("${proc[detailed_mem_int]}")
					fi

					#* Remove selected process from array if process is excluded by filtering or not on first page
					if [[ -n $filter && ! ${proc[detailed_name]} =~ $filter ]]; then
						unset 'proc_array[count]'
						cpu_int=0; pid_count=0
					fi
				fi

				#* Create small graphs for all visible processes using more than 1% cpu time
				if [[ ${cpu_int} -gt 0 ]]; then pid_count=5; fi

				if [[ -z ${!pid_graph} && ${cpu_int} -gt 0 ]]; then
						tmp_value_array=("$((cpu_int+4))")
					create_mini_graph -o "pid_${pid}_graph" -nc -w 5 "tmp_value_array"
				elif [[ ${pid_count} -gt 0 ]]; then
					if [[ ${cpu_int} -gt 9 ]]; then
						create_mini_graph -nc -add-value "pid_${pid}_graph" "$((cpu_int+20))"
					else
						create_mini_graph -nc -add-value "pid_${pid}_graph" "$((cpu_int+4))"
					fi
					
					pid_count=$((${pid_count}-1))
				elif [[ ${pid_count} == "0" ]]; then
					unset "pid_${pid}_graph"
					unset "pid_${pid}_count"
				fi
			else
				tmp_percent="${proc_array[count]:(-5)}"; tmp_percent="${tmp_percent// /}"; if [[ ${tmp_percent//./} != "$tmp_percent" ]]; then tmp_percent="${tmp_percent::-2}"; fi
				if ((tmp_percent>100)); then
					proc_array[count]="${proc_array[count]::-5}  100"
				fi
			fi

			proc[old_${pid}_ticks]=${proc[new_${pid}_ticks]}
			
		fi

		if ((breaking==1)); then 
			if [[ ${proc[detailed]} == "1" && -z ${proc[detailed_cpu]} ]] && ps ${proc[detailed_pid]} >/dev/null 2>&1; then
				readarray ${options} -O ${#proc_array[@]} proc_array < <(ps -o pid:${proc[pid_len]}=Pid:,comm:${format_cmd}=Program:${format_args},nlwp:3=Tr:,euser:6=User:,pmem=Mem%,pcpu:10=Cpu% --no-headers -p ${proc[detailed_pid]} || true)
			else
				break
			fi
		fi

	done


	proc[old_timestamp]=${proc[new_timestamp]}

	if ((proc[detailed]==1)) && [[ -z ${proc[detailed_cpu]} && -z ${proc[detailed_killed]} ]]; then proc[detailed_killed]=1; proc[detailed_change]=1
	elif [[ -n ${proc[detailed_cpu]} ]]; then unset 'proc[detailed_killed]'; fi

	#* Sort output array based on cpu usage if "cpu responsive" is selected
	if [[ ${proc_sorting} == "cpu responsive" ]]; then
		local -a sort_array
		if [[ -z ${proc[reverse]} ]]; then local sort_rev="-r"; fi
		sort_array[0]="${proc_array[0]}"
		readarray -O 1 -t sort_array < <(printf "%s\n" "${proc_array[@]:1}" | awk '{ print $NF, $0 }' | sort -n -k1 ${sort_rev}| sed 's/^[0-9\.]* //')
		proc_array=("${sort_array[@]}")
	fi

	#* Clear up memory by removing variables and graphs of no longer running processes
	((++proc[general_counter]))
	if ((proc[general_counter]>100)); then
		proc[general_counter]=0
		for ((i=0;i<${#pid_history[@]};i++)); do
			if [[ -n ${pid_history[$i]} && ! -e /proc/${pid_history[$i]} ]]; then
				unset "pid_${pid_history[$i]}_graph"
				unset "pid_${pid_history[$i]}_count"
				unset "proc[new_${pid_history[$i]}_ticks]"
				unset "proc[old_${pid_history[$i]}_ticks]"
				unset "pid_history[${i}]"
			fi
		done
		pid_history=(${pid_history[@]})
	fi

}

collect_net() { #? Collect information from "/proc/net/dev"
	local operations operation direction index unit_selector speed speed_B total
	local -a net_dev history_sorted history_last

	if [[ $1 == "init" ]]; then 
		for direction in "download" "upload"; do
		net[${direction}_max]=0
		net[${direction}_new_low]=0
		net[${direction}_new_max]=0
		net[${direction}_max_current]=0
		net[${direction}_graph_max]=$((50<<10))
		done
	fi

	#* Get the line with relevant net device from /proc/net/dev into array net_dev, index 1 is download, index 9 is upload
	get_value -map net_dev -sf "/proc/net/dev" -k "${net[device]}" -a

	#* Timestamp the values to accurately calculate values in seconds
	get_ms net[new_timestamp]
	for direction in "download" "upload"; do
		if [[ $direction == "download" ]]; then index=1
		else index=9; fi

		net[new_${direction}]=${net_dev[index]}

		if [[ -n ${net[old_${direction}]} ]]; then
			#* Get total, convert to floating point and format string to best fitting unit in Bytes
			floating_humanizer -Byte -v net[total_${direction}] ${net[new_${direction}]}
			
			#* Calculate current speeds: ("New value" - "Old value") * 1000(for ms to seconds) / ("new_timestamp" - "old_timestamp")
			net[speed_${direction}]=$(( (${net[new_${direction}]}-${net[old_${direction}]})*1000/(net[new_timestamp]-net[old_timestamp]) ))

			#* Convert to floating point and format string to best fitting unit in Bytes and Bits per second
			floating_humanizer -Byte -per-second -v net[speed_${direction}_byteps] ${net[speed_${direction}]}
			floating_humanizer -bit -per-second -v net[speed_${direction}_bitps] ${net[speed_${direction}]}

			#* Update download and upload max values for graph
			if ((${net[speed_${direction}]}>${net[${direction}_max]})); then
				net[${direction}_max]=${net[speed_${direction}]}
			fi

			if ((${net[speed_${direction}]}>${net[${direction}_graph_max]})); then
					((++net[${direction}_new_max]))
					if ((net[${direction}_new_low]>0)); then ((net[${direction}_new_low]--)); fi
			elif ((${net[${direction}_graph_max]}>10<<10 & ${net[speed_${direction}]}<${net[${direction}_graph_max]}/8)); then
				((++net[${direction}_new_low]))
				if ((net[${direction}_new_max]>0)); then ((net[${direction}_new_max]--)); fi
			# else
			# 	net[${direction}_new_low]=0
			# 	net[${direction}_new_max]=0
			fi

			#* Copy download and upload speed to history arrays and trim earlier entries
			local -n history="net_history_${direction}"
			if ((${#history[@]}>box[net_width]*2)); then
				history=( "${history[@]:${box[net_width]}}" "${net[speed_${direction}]}")
			else
				history+=("${net[speed_${direction}]}")
			fi

			#* Check for new max value and set flag to adjust resolution of graph if needed
			if ((${net[${direction}_new_max]}>=5)); then
				net[${direction}_graph_max]=$((${net[${direction}_max]}+(${net[${direction}_max]}/2) ))
				net[${direction}_redraw]=1
				net[${direction}_new_max]=0

			#* If current max value isn't relevant, sort array to get the next largest value to set graph resolution
			elif ((${net[${direction}_new_low]}>=5 & ${#history[@]}>5)); then
				history_last=("${history[@]:(-5)}")
				sort_array_int "history_last" "history_sorted"
				net[${direction}_max]=${history_sorted[0]}
				net[${direction}_graph_max]=$(( ${net[${direction}_max]}*3 ))
				if ((${net[${direction}_graph_max]}<10<<10)); then net[${direction}_graph_max]=$((10<<10)); fi
				net[${direction}_redraw]=1
				net[${direction}_new_low]=0
			fi	
		fi

		net[old_${direction}]=${net[new_${direction}]}
	done

	net[old_timestamp]=${net[new_timestamp]}

}

calc_sizes() { #? Calculate width and height of all boxes
	local pos calc_size calc_total percent threads=${cpu[threads]}
	
	#* Calculate heights
	for pos in ${box[boxes]/processes/}; do
		if [[ $pos = "cpu" ]]; then percent=32; 
		elif [[ $pos = "mem" ]]; then percent=40; 
		else percent=28; fi

		#* Multiplying with 10 to convert to floating point
		calc_size=$(( (tty_height*10)*(percent*10)/100 ))

		#* Round down if last 2 digits of value is below "50" and round up if above
		if ((${calc_size:(-2):1}==0)); then calc_size=$((calc_size+10)); fi
		if ((${calc_size:(-2)}<50)); then
			calc_size=$((${calc_size::-2}))
		else 
			calc_size=$((${calc_size::-2}+1))
		fi

		#* Subtract from last value if the total of all rounded numbers is larger then terminal height
		while ((calc_total+calc_size>tty_height)); do ((--calc_size)); done
		calc_total=$((calc_total+calc_size))

		#* Set calculated values in box array
		box[${pos}_line]=$((calc_total-calc_size+1))
		box[${pos}_col]=1
		box[${pos}_height]=$calc_size
		box[${pos}_width]=$tty_width
	done


	#* Calculate widths
	unset calc_total
	for pos in net processes; do
		if [[ $pos = "net" ]]; then percent=45; else percent=55; fi
		
		#* Multiplying with 10 to convert to floating point
		calc_size=$(( (tty_width*10)*(percent*10)/100 ))

		#* Round down if last 2 digits of value is below "50" and round up if above
		if ((${calc_size:(-2)}<50)); then
			calc_size=$((${calc_size::-2}))
		else 
			calc_size=$((${calc_size::-2}+1))
		fi

		#* Subtract from last value if the total of all rounded numbers is larger then terminal width
		while ((calc_total+calc_size>tty_width)); do ((--calc_size)); done
		calc_total=$((calc_total+calc_size))

		#* Set calculated values in box array
		box[${pos}_col]=$((calc_total-calc_size+1))
		box[${pos}_width]=$calc_size
	done

	#* Copy numbers around to get target layout
	box[mem_width]=${box[net_width]}
	box[processes_line]=${box[mem_line]}
	box[processes_height]=$((box[mem_height]+box[net_height]))

	#  threads=${box[testing]} #! For testing, remove <--------------

	#* Recalculate size of process box if currently showing detailed process information
	if ((proc[detailed]==1)); then
		box[details_line]=${box[processes_line]}
		box[details_col]=${box[processes_col]}
		box[details_width]=${box[processes_width]}
		box[details_height]=8
		box[processes_line]=$((box[processes_line]+box[details_height]))
		box[processes_height]=$((box[processes_height]-box[details_height]))
	fi
	
	#* Calculate number of columns and placement of cpu meter box
	local cpu_line=$((box[cpu_line]+1)) cpu_width=$((box[cpu_width]-2)) cpu_height=$((box[cpu_height]-2)) box_cols
	if ((threads>(cpu_height-3)*3 && tty_width>=200)); then box[p_width]=$((24*4)); box[p_height]=$((threads/4+4)); box_cols=4
	elif ((threads>(cpu_height-3)*2 && tty_width>=150)); then box[p_width]=$((24*3)); box[p_height]=$((threads/3+5)); box_cols=3
	elif ((threads>cpu_height-3 && tty_width>=100)); then box[p_width]=$((24*2)); box[p_height]=$((threads/2+4)); box_cols=2
	else box[p_width]=24; box[p_height]=$((threads+4)); box_cols=1
	fi

	if [[ $check_temp == true ]]; then
		box[p_width]=$(( box[p_width]+13*box_cols))
	fi
	
	if ((box[p_height]>cpu_height)); then box[p_height]=$cpu_height; fi	
	box[p_col]="$((cpu_width-box[p_width]+2))"
	box[p_line]="$((cpu_line+(cpu_height/2)-(box[p_height]/2)+1))"

	#* Calculate placement of mem divider
	local mem_line=$((box[mem_line]+1)) mem_width=$((box[mem_width]-2)) mem_height=$((box[mem_height]-2)) mem_col=$((box[mem_col]+1))
	box[m_width]=$((mem_width/2))
	box[m_width2]=${box[m_width]}
	if ((box[m_width]+box[m_width2]<mem_width)); then ((box[m_width]++)); fi
	box[m_height]=$mem_height
	box[m_col]=$((mem_col+1))
	box[m_line]=$mem_line

	#* Calculate placement of net value box
	local net_line=$((box[net_line]+1)) net_width=$((box[net_width]-2)) net_height=$((box[net_height]-2))
	box[n_width]=24
	if ((net_height>9)); then box[n_height]=9
	else box[n_height]=$net_height; fi
	box[n_col]="$((net_width-box[n_width]+2))"
	box[n_line]="$((net_line+(net_height/2)-(box[n_height]/2)+1))"
	

}

draw_bg() { #? Draw all box outlines
	local this_box cpu_p_width i cpu_model_len

	unset boxes_out
	for this_box in ${box[boxes]}; do
		create_box -v boxes_out -col ${box[${this_box}_col]} -line ${box[${this_box}_line]} -width ${box[${this_box}_width]} -height ${box[${this_box}_height]} -fill -lc "${box[${this_box}_color]}" -title ${this_box}
	done

	#* Misc cpu box
	if [[ $check_temp == true ]]; then cpu_model_len=18; else cpu_model_len=9; fi
	create_box -v boxes_out -col $((box[p_col]-1)) -line $((box[p_line]-1)) -width ${box[p_width]} -height ${box[p_height]} -lc ${theme[div_line]} -t "${cpu[model]:0:${cpu_model_len}}"
	print -v boxes_out -m ${box[cpu_line]} $((box[cpu_col]+10)) -rs \
	-fg ${box[cpu_color]} -t "┤" -b -fg ${theme[hi_fg]} -t "m" -fg ${theme[title]} -t "enu" -rs -fg ${box[cpu_color]} -t "├"

	#* Misc mem
	print -v boxes_out -m ${box[mem_line]} $((box[mem_col]+box[m_width]+2)) -rs -fg ${box[mem_color]} -t "┤" -fg ${theme[title]} -b -t "disks" -rs -fg ${box[mem_color]} -t "├"
	print -v boxes_out -m ${box[mem_line]} $((box[mem_col]+box[m_width])) -rs -fg ${box[mem_color]} -t "┬"
	print -v boxes_out -m $((box[mem_line]+box[mem_height]-1)) $((box[mem_col]+box[m_width])) -fg ${box[mem_color]} -t "┴"
	for((i=1;i<=box[mem_height]-2;i++)); do
		print -v boxes_out -m $((box[mem_line]+i)) $((box[mem_col]+box[m_width])) -fg ${theme[div_line]} -t "│"
	done


	#* Misc net box
	create_box -v boxes_out -col $((box[n_col]-1)) -line $((box[n_line]-1)) -width ${box[n_width]} -height ${box[n_height]} -lc ${theme[div_line]} -t "Download"
	print -v boxes_out -m $((box[n_line]+box[n_height]-2)) $((box[n_col]+1)) -rs -fg ${theme[div_line]} -t "┤" -fg ${theme[title]} -b -t "Upload" -rs -fg ${theme[div_line]} -t "├"


	if [[ $1 == "quiet" ]]; then draw_out="${boxes_out}"
	else echo -en "${boxes_out}"; fi
	draw_update_string $1
}

draw_cpu() { #? Draw cpu and core graphs and print percentages
	local cpu_out i name cpu_p_color temp_color y pt_line pt_col p_normal_color="${theme[main_fg]}" threads=${cpu[threads]}
	local meter meter_size meter_width temp_var cpu_out_var core_name temp_name temp_width

	#* Get variables from previous calculations
	local col=$((box[cpu_col]+1)) line=$((box[cpu_line]+1)) width=$((box[cpu_width]-2)) height=$((box[cpu_height]-2))
	local p_width=${box[p_width]} p_height=${box[p_height]} p_col=${box[p_col]} p_line=${box[p_line]}
	
	#* If resized recreate cpu meter/graph box, cpu graph and core graphs
	if ((resized>0)); then
		local graph_a_size graph_b_size
		graph_a_size=$((height/2)); graph_b_size=${graph_a_size}
		
		if ((graph_a_size*2<height)); then ((graph_a_size++)); fi
		create_graph -o cpu_graph_a -d ${line} ${col} ${graph_a_size} $((width-p_width-2)) -c color_cpu_graph -n cpu_history
		create_graph -o cpu_graph_b -d $((line+graph_a_size)) ${col} ${graph_b_size} $((width-p_width-2)) -c color_cpu_graph -i -n cpu_history
		
		for((i=1;i<=threads;i++)); do
			create_mini_graph -o "cpu_core_graph_$i" -w 10 -c color_cpu_graph "cpu_core_history_$i"
		done

		if [[ $check_temp == true ]]; then
			for((i=0;i<=threads;i++)); do
				create_mini_graph -o "cpu_temp_graph_$i" -w 5 -c color_temp_graph "cpu_temp_history_$i"
			done
		fi
		((resized++))
	fi

	#* Add new values to cpu and core graphs unless just resized
	if ((resized==0)); then
		create_graph -add-last cpu_graph_a cpu_history
		create_graph -i -add-last cpu_graph_b cpu_history
		for((i=1;i<=threads;i++)); do
			declare -n core_hist="cpu_core_history_${i}[-1]"
			create_mini_graph -w 10 -c color_cpu_graph -add-value "cpu_core_graph_$i" ${core_hist}
		done
		if [[ $check_temp == true ]]; then
			for((i=0;i<=threads;i++)); do
				declare -n temp_hist="cpu_temp_history_${i}[-1]"
				create_mini_graph -w 5 -c color_temp_graph -add-value "cpu_temp_graph_$i" ${temp_hist}
			done
		fi
	fi

	#* Print CPU total and all cpu core percentage meters in box
	for((i=0;i<=threads;i++)); do
		if ((i==0)); then name="CPU"; else name="Core${i}"; fi
		
		#* Get color of cpu text depending on current usage
		cpu_p_color="${color_cpu_graph[cpu_usage[i]]}" 
		
		pt_col=$p_col; pt_line=$p_line; meter_size="small"; meter_width=10
		
		#* Set temperature string if "sensors" is available
		if [[ $check_temp == true ]]; then
			#* Get color of temperature text depending on current temp vs factory high temp
			declare -n temp_hist="cpu_temp_history_${i}[-1]"
			temp_color="${color_temp_graph[${temp_hist}]}"
			temp_name="cpu_temp_graph_$i"
			temp_width=13
		fi

		if ((i==0 & p_width>24+temp_width)); then 
			name="CPU Total "; meter_width=$((p_width-17-temp_width))
		fi
		

		#* Create cpu usage meter
		if ((i==0)); then
			create_meter -v meter -w $meter_width -f -c color_cpu_graph ${cpu_usage[i]}
		else
			core_name="cpu_core_graph_$i"
			meter="${!core_name}"
		fi
		
		if ((p_width>84+temp_width & i>=(p_height-2)*3-2)); then pt_line=$((p_line+i-y*4)); pt_col=$((p_col+72+temp_width*3))
		elif ((p_width>54+temp_width & i>=(p_height-2)*2-1)); then pt_line=$((p_line+i-y*3)); pt_col=$((p_col+48+temp_width*2))
		elif ((p_width>24+temp_width & i>=p_height-2)); then pt_line=$((p_line+i-y*2)); pt_col=$((p_col+24+temp_width))
		else y=$i; fi

		print -v cpu_out_var -m $((pt_line+y)) $pt_col -rs -fg $p_normal_color -jl 7 -t "$name" -fg ${theme[inactive_fg]} "⡀⡀⡀⡀⡀⡀⡀⡀⡀⡀" -l 10 -t "$meter"\
		-fg $cpu_p_color -jr 4 -t "${cpu_usage[i]}" -fg $p_normal_color -t "%"
		if [[ $check_temp == true ]]; then
			print -v cpu_out_var -fg ${theme[inactive_fg]} "  ⡀⡀⡀⡀⡀" -l 7 -t "  ${!temp_name}" -fg $temp_color -jr 4 -t ${cpu[temp_${i}]} -fg $p_normal_color -t ${cpu[temp_unit]}
		fi

		if (( i>(p_height-2)*( p_width/(24+temp_width) )-( p_width/(24+temp_width) )-1 )); then break; fi	
	done

	#* Print load average and uptime
	if ((pt_line+y+3<p_line+p_height)); then
		local avg_string avg_width
		if [[ $check_temp == true ]]; then avg_string="Load Average: "; avg_width=7; else avg_string="L AVG: "; avg_width=5; fi
		print -v cpu_out_var -m $((pt_line+y+1)) $pt_col -fg ${theme[main_fg]} -t "${avg_string}"
		for avg_string in ${cpu[load_avg]}; do
			print -v cpu_out_var -jc $avg_width -t "${avg_string::4}"
		done
	fi
	print -v cpu_out_var -m $((line+height-1)) $((col+1)) -fg ${theme[inactive_fg]} -trans -t "up ${cpu[uptime]}"

	#* Print current CPU frequency right of the title in the meter box
	if [[ -n ${cpu[freq_string]} ]]; then print -v cpu_out_var -m $((p_line-1)) $((p_col+p_width-5-${#cpu[freq_string]})) -fg ${theme[div_line]} -t "┤" -fg ${theme[title]} -b -t "${cpu[freq_string]}" -rs -fg ${theme[div_line]} -t "├"; fi
	
	#* Print created text, graph and meters to output variable
	draw_out+="${cpu_graph_a[*]}${cpu_graph_b[*]}${cpu_out_var}"

}

draw_mem() { #? Draw mem, swap and disk statistics

	if ((mem[counter]>0 & resized==0)); then return; fi

	local i swap_used_meter swap_free_meter mem_available_meter mem_free_meter mem_used_meter mem_cached_meter normal_color="${theme[main_fg]}" value_text
	local meter_mod_w meter_mod_pos value type m_title meter_options
	local -a types=("mem")
	unset mem_out

	if [[ -n $swap_on ]]; then types+=("swap"); fi

	#* Get variables from previous calculations
	local col=$((box[mem_col]+1)) line=$((box[mem_line]+1)) width=$((box[mem_width]-2)) height=$((box[mem_height]-2))
	local m_width=${box[m_width]} m_height=${box[m_height]} m_col=${box[m_col]} m_line=${box[m_line]} mem_line=$((box[mem_col]+box[m_width]))

	#* Create text and meters for memory and swap and adapt sizes based on available height
	local y_pos=$m_line v_height=8 list value meter inv_meter
	for type in ${types[@]}; do
		local -n type_name="$type"
		if [[ $type == "mem" ]]; then 
			m_title="memory"
		else 
			m_title="$type"
			if ((height>14)); then ((y_pos++)); fi
		fi

		#* Print name of type and total amount in humanized base 2 bytes
		print -v mem_out -m $y_pos $m_col -rs -fg ${theme[title]} -b -jl 9 -t "${m_title^}:" -m $((y_pos++)) $((mem_line-10)) -jr 9 -trans -t " ${type_name[total_string]::$((m_width-11))}"

		for value in "used" "available" "cached" "free"; do
			if [[ $type == "swap" && $value == "available" ]]; then value="free"
			elif [[ $type == "swap" && $value == "cached" ]]; then break 2; fi

			value_text="${value::$((m_width-12))}"
			if ((height<14)); then value_text="${value_text::5}"; fi
			
			#* Print name of value and value amount in humanized base 2 bytes
			print -v mem_out -m $y_pos $m_col -rs -fg $normal_color -jl 9 -t "${value_text^}:" -m $((y_pos++)) $((mem_line-10)) -jr 9 -trans -t " ${type_name[${value}_string]::$((m_width-11))}"
			
			#* Create meter for value and calculate size and placement depending on terminal size
			if ((height>v_height++ | tty_width>100)); then
				if ((height<=v_height & tty_width<150)); then
					meter_mod_w=12
					meter_mod_pos=7
					((y_pos--))
				elif ((height<=v_height)); then
					print -v mem_out -m $((--y_pos)) $((m_col+5)) -jr 4 -t "${type_name[${value}_percent]}%"
					meter_mod_w=14
					meter_mod_pos=10
				fi
				create_meter -v ${type}_${value}_meter -w $((m_width-7-meter_mod_w)) -f -c color_${value}_graph ${type_name[${value}_percent]}
				
				meter="${type}_${value}_meter"
				print -v mem_out -m $((y_pos++)) $((m_col+meter_mod_pos)) -t "${!meter}" -rs -fg $normal_color

				if [[ -z $meter_mod_w ]]; then print -v mem_out  -jr 4 -t "${type_name[${value}_percent]}%"; fi
			fi
		done
	 done


	#* Create text and meters for disks and adapt sizes based on available height
	local disk_num disk_name disk_value v_height2
	y_pos=$m_line
	m_col=$((m_col+m_width))
	m_width=${box[m_width2]}
	v_height=$((${#disks_name[@]}))
	unset meter_mod_w meter_mod_pos

	for disk_name in "${disks_name[@]}"; do
		if ((y_pos>m_line+height-2)); then break; fi

		#* Print folder disk is mounted on and total size in humanized base 2 bytes
		print -v mem_out -m $((y_pos++)) $m_col -rs -fg ${theme[title]} -b -jl 9 -t "${disks_name[disk_num]::10}" -jr $((m_width-11)) -t "${disks_total[disk_num]::$((m_width-11))}"

		for value in "used" "free"; do
			if ((height<v_height*3)) && [[ $value == "free" ]]; then break; fi
			local -n disk_value="disks_${value}"

			#* Print name of value and value amount in humanized base 2 bytes
			print -v mem_out -m $((y_pos++)) $m_col -rs -fg $normal_color -jl 9 -t "${value^}:" -jr $((m_width-11)) -t "${disk_value[disk_num]::$((m_width-11))}"

			#* Create meter for value and calculate size and placement depending on terminal size
			if ((height>=v_height*5 | tty_width>100)); then
				local -n disk_value_percent="disks_${value}_percent"
				if ((height<=v_height*5 & tty_width<150)); then
					meter_mod_w=12
					meter_mod_pos=7
					((y_pos--))
				elif ((height<=v_height*5)); then
					print -v mem_out -m $((--y_pos)) $((m_col+5)) -jr 4 -t "${disk_value_percent[disk_num]}%"
					meter_mod_w=14
					meter_mod_pos=10
				fi
				create_meter -v disk_${disk_num}_${value}_meter -w $((m_width-7-meter_mod_w)) -f -c color_${value}_graph ${disk_value_percent[disk_num]}

				meter="disk_${disk_num}_${value}_meter"
				print -v mem_out -m $((y_pos++)) $((m_col+meter_mod_pos)) -t "${!meter}" -rs -fg $normal_color

				if [[ -z $meter_mod_w ]]; then print -v mem_out -jr 4 -t "${disk_value_percent[disk_num]}%"; fi
			fi
			if ((y_pos>m_line+height-1)); then break; fi
		done
		if ((height>=v_height*4 & height<v_height*5 | height>=v_height*6)); then ((y_pos++)); fi
		((++disk_num))
	done

	if ((resized>0)); then ((resized++)); fi
	#* Print created text, graph and meters to output variable
	draw_out+="${mem_graph[*]}${swap_graph[*]}${mem_out}"

}

draw_processes() { #? Draw processes and values to screen
	local argument="$1"
	if [[ -n $skip_process_draw && $argument != "now" ]]; then return; fi
	local line=${box[processes_line]} col=${box[processes_col]} width=${box[processes_width]} height=${box[processes_height]} out_line y=1 fg_step_r=0 fg_step_g=0 fg_step_b=0 checker=2 page_string
	local reverse_string reverse_pos order_left="───────────┤" filter_string current_num detail_location det_no_add com_fg pg_arrow_up_fg pg_arrow_down_fg
	local pid=0 pid_graph pid_step_r pid_step_g pid_step_b pid_add_r pid_add_g pid_add_b bg_add bg_step proc_start up_fg down_fg page_up_fg page_down_fg this_box=processes
	local d_width=${box[details_width]} d_height=${box[details_height]} d_line=${box[details_line]} d_col=${box[details_col]}
	local detail_graph_width=$((d_width/3+2)) detail_graph_height=$((d_height-1)) kill_fg det_mod fg_add_r fg_add_g fg_add_b
	local right_width=$((d_width-detail_graph_width-2))
	local right_col=$((d_col+detail_graph_width+4))
	local -a pid_rgb=(${theme[proc_misc]}) fg_rgb=(${theme[main_fg_dec]})
	local pid_r=${pid_rgb[0]} pid_g=${pid_rgb[1]} pid_b=${pid_rgb[2]} fg_r=${fg_rgb[0]} fg_g=${fg_rgb[1]} fg_b=${fg_rgb[2]}

	if [[ $argument == "now" ]]; then skip_process_draw=1; fi

	fg_add_r=$(( (fg_r-(fg_r/6) )/height))
	fg_add_g=$(( (fg_g-(fg_g/6) )/height))
	fg_add_b=$(( (fg_b-(fg_b/6) )/height))

	pid_add_r=$(( (pid_r-(pid_r/6) )/height))
	pid_add_g=$(( (pid_g-(pid_g/6) )/height))
	pid_add_b=$(( (pid_b-(pid_b/6) )/height))

	unset proc_out

	#* Details box
	if ((proc[detailed_change]>0)) || ((proc[detailed]>0 & resized>0)); then
		proc[detailed_change]=0
		proc[order_change]=1
		proc[page_change]=1
		if ((proc[detailed]==1)); then
			unset proc_det
			local enter_fg enter_a_fg misc_fg misc_a_fg i det_y=6 dets cmd_y

			if [[ ${#detail_history[@]} -eq 1 ]] || ((resized>0)); then
				unset proc_det2 
				create_graph -o detail_graph -d $((d_line+1)) $((d_col+1)) ${detail_graph_height} ${detail_graph_width} -c color_cpu_graph -n detail_history
				if ((tty_width>120)); then create_mini_graph -o detail_mem_graph -w $((right_width/3-3)) -nc detail_mem_history; fi
				det_no_add=1
			
				for detail_location in "${d_line}" "$((d_line+d_height))"; do
					print -v proc_det2 -m ${detail_location} $((d_col+1)) -rs -fg ${box[processes_color]} -rp $((d_width-2)) -t "─"
				done
				for((i=1;i<d_height;i++)); do
					print -v proc_det2 -m $((d_line+i)) $((d_col+3+detail_graph_width)) -rp $((right_width-1)) -t " "
					print -v proc_det2 -m $((d_line+i)) ${d_col} -fg ${box[processes_color]} -t "│" -r $((detail_graph_width+1)) -fg ${theme[div_line]} -t "│" -r $((right_width+1)) -fg ${box[processes_color]} -t "│"
				done

				print -v proc_det2 -m ${d_line} ${d_col} -t "┌" -m ${d_line} $((d_col+d_width)) -t "┐"
				print -v proc_det2 -m ${d_line} $((d_col+2+detail_graph_width)) -t "┬" -m $((d_line+d_height)) $((d_col+detail_graph_width+2)) -t "┴"
				print -v proc_det2 -m $((d_line+d_height)) ${d_col} -t "├" -r 1 -t "┤" -fg ${theme[title]} -b -t "${this_box}" -rs -fg ${box[processes_color]} -t "├" -r $((d_width-5-${#this_box})) -t "┤"
				print -v proc_det2 -m ${d_line} $((d_col+2)) -t "┤" -fg ${theme[title]} -b -t "${proc[detailed_name],,}" -rs -fg ${box[processes_color]} -t "├"
				if ((tty_width>128)); then print -v proc_det2 -m -r 1 -t "┤" -fg ${theme[title]} -b -t "${proc[detailed_pid]}" -rs -fg ${box[processes_color]} -t "├"; fi


				
				if ((${#proc[detailed_cmd]}>(right_width-6)*2)); then ((det_y--)); dets=2
				elif ((${#proc[detailed_cmd]}>right_width-6)); then dets=1; fi
				
				print -v proc_det2 -fg ${theme[title]} -b
				for i in C M D; do
					print -v proc_det2 -m $((d_line+5+cmd_y++)) $right_col -t "$i"
				done
				
				
				print -v proc_det2 -m $((d_line+det_y++)) $((right_col+1)) -jc $((right_width-4)) -rs -fg ${theme[main_fg]} -t "${proc[detailed_cmd]::$((right_width-6))}"
				if ((dets>0)); then print -v proc_det2 -m $((d_line+det_y++)) $((right_col+2)) -jl $((right_width-6)) -t "${proc[detailed_cmd]:$((right_width-6)):$((right_width-6))}"; fi
				if ((dets>1)); then print -v proc_det2 -m $((d_line+det_y)) $((right_col+2)) -jl $((right_width-6)) -t "${proc[detailed_cmd]:$(( (right_width-6)*2 )):$((right_width-6))}"; fi
				
			fi
			
			
			if ((proc[selected]>0)); then enter_fg="${theme[inactive_fg]}"; enter_a_fg="${theme[inactive_fg]}"; else enter_fg="${theme[title]}"; enter_a_fg="${theme[hi_fg]}"; fi
			if [[ -n ${proc[detailed_killed]} ]]; then misc_fg="${theme[title]}"; misc_a_fg="${theme[hi_fg]}"
			else misc_fg=$enter_fg; misc_a_fg=$enter_a_fg; fi
			print -v proc_det -m ${d_line} $((d_col+d_width-11)) -fg ${box[processes_color]} -t "┤" -fg $enter_fg -b -t "close " -fg $enter_a_fg -t "↲" -rs -fg ${box[processes_color]} -t "├"
			if ((tty_width<129)); then det_mod="-8"; fi
			
			print -v proc_det -m ${d_line} $((d_col+detail_graph_width+4+det_mod)) -t "┤" -fg $misc_a_fg -b -t "t" -fg $misc_fg -t "erminate" -rs -fg ${box[processes_color]} -t "├"
			print -v proc_det -r 1 -t "┤" -fg $misc_a_fg -b -t "k" -fg $misc_fg -t "ill" -rs -fg ${box[processes_color]} -t "├"
			if ((tty_width>104)); then print -v proc_det -r 1 -t "┤" -fg $misc_a_fg -b -t "i" -fg $misc_fg -t "nterrupt" -rs -fg ${box[processes_color]} -t "├"; fi
			

			proc_det="${proc_det2}${proc_det}"
			proc_out="${proc_det}"

		elif ((resized==0)); then
			unset proc_det
			create_box -v proc_out -col ${box[${this_box}_col]} -line ${box[${this_box}_line]} -width ${box[${this_box}_width]} -height ${box[${this_box}_height]} -fill -lc "${box[${this_box}_color]}" -title ${this_box}
		fi	
	fi

	if [[ ${proc[detailed]} -eq 1 ]]; then
		local det_status status_color det_columns=3
		if ((tty_width>140)); then ((det_columns++)); fi
		if ((tty_width>150)); then ((det_columns++)); fi
		if [[ -z $det_no_add && $1 != "now" && -z ${proc[detailed_killed]} ]]; then 
			create_graph -add-last detail_graph detail_history
			if ((tty_width>120)); then create_mini_graph -w $((right_width/3-3)) -nc -add-last detail_mem_graph detail_mem_history; fi
		fi
		
		print -v proc_out -fg ${theme[title]} -b
		cmd_y=0
		for i in C P U; do
			print -v proc_out -m $((d_line+3+cmd_y++)) $((d_col+1)) -t "$i"
		done
		print -v proc_out -m $((d_line+1)) $((d_col+1)) -fg ${theme[title]} -t "${proc[detailed_cpu]}%"
		
		if [[ -n ${proc[detailed_killed]} ]]; then det_status="stopped"; status_color="${theme[inactive_fg]}"
		else det_status="running"; status_color="${theme[proc_misc]}"; fi
		print -v proc_out -m $((d_line+1)) ${right_col} -fg ${theme[title]} -b -jc $((right_width/det_columns-1)) -t "Status:" -jc $((right_width/det_columns)) -t "Elapsed:" -jc $((right_width/det_columns)) -t "Parent:"
		if ((det_columns>=4)); then print -v proc_out -jc $((right_width/det_columns-1)) -t "User:"; fi
		if ((det_columns>=5)); then print -v proc_out -jc $((right_width/det_columns-1)) -t "Threads:"; fi
		print -v proc_out -m $((d_line+2)) ${right_col} -rs -fg ${status_color} -jc $((right_width/det_columns-1)) -t "${det_status}" -jc $((right_width/det_columns)) -fg ${theme[main_fg]} -t "${proc[detailed_runtime]::$((right_width/det_columns-1))}" -jc $((right_width/det_columns)) -t "${proc[detailed_parent_name]::$((right_width/det_columns-2))}"
		if ((det_columns>=4)); then print -v proc_out -jc $((right_width/det_columns-1)) -t "${proc[detailed_user]::$((right_width/det_columns-2))}"; fi
		if ((det_columns>=5)); then print -v proc_out -jc $((right_width/det_columns-1)) -t "${proc[detailed_threads]}"; fi

		print -v proc_out -m $((d_line+4)) ${right_col} -fg ${theme[title]} -b -jr $((right_width/3+2)) -t "Memory: ${proc[detailed_mem]}%" -t " " 
		if ((tty_width>120)); then print -v proc_out -rs -fg ${theme[inactive_fg]} -rp $((right_width/3-3)) "⡀" -l $((right_width/3-3)) -fg ${theme[proc_misc]} -t "${detail_mem_graph}" -t " "; fi
		print -v proc_out -fg ${theme[title]} -b -t "${proc[detailed_mem_string]}"
	fi


	if ((proc[page]==1)); then proc_start=1
	else proc_start=$(( (height-3)*(proc[page]-1)+1 )); fi

	if ((proc_start+proc[selected]>${#proc_array[@]})); then proc[selected]=$((${#proc_array[@]}-proc_start)); fi

	if ((proc[selected]>1)); then
		fg_r="$(( fg_r-( fg_add_r*(proc[selected]-1) ) ))"
		fg_g="$(( fg_g-( fg_add_g*(proc[selected]-1) ) ))"
		fg_b="$(( fg_b-( fg_add_b*(proc[selected]-1) ) ))"

		pid_r="$(( pid_r-( pid_add_r*(proc[selected]-1) ) ))"
		pid_g="$(( pid_g-( pid_add_g*(proc[selected]-1) ) ))"
		pid_b="$(( pid_b-( pid_add_b*(proc[selected]-1) ) ))"
	fi
 
	current_num=1
	
	print -v proc_out -rs -m $((line+y++)) $((col+1)) -fg ${theme[title]} -b -t "${proc_array[0]::$((width-3))} " -rs


	for out_line in "${proc_array[@]:$proc_start}"; do
		pid="${out_line::$((proc[pid_len]+1))}"; pid="${pid// /}"
		pid_graph="pid_${pid}_graph"

		if ((current_num==proc[selected])); then print -v proc_out -bg ${theme[selected_bg]} -fg ${theme[selected_fg]} -b; proc[selected_pid]="$pid"
		else print -v proc_out -rs -fg $((fg_r-fg_step_r)) $((fg_b-fg_step_b)) $((fg_b-fg_step_b)); fi
	
		print -v proc_out -m $((line+y)) $((col+1)) -t "${out_line::$((width-3))} "
		
		if ((current_num==proc[selected])); then print -v proc_out -rs -bg ${theme[selected_bg]}; fi
		
		print -v proc_out -m $((line+y)) $((col+width-12)) -fg ${theme[inactive_fg]} -t "⡀⡀⡀⡀⡀"

		if [[ -n ${!pid_graph} ]]; then
			print -v proc_out -m $((line+y)) $((col+width-12)) -fg $((pid_r-pid_step_r)) $((pid_g-pid_step_g)) $((pid_b-pid_step_b)) -t "${!pid_graph}"
		fi
		
		((y++))
		((current_num++))
		if ((y>height-2)); then break; fi
		if ((current_num<proc[selected]+1)); then
			fg_step_r=$((fg_step_r-fg_add_r)); fg_step_g=$((fg_step_g-fg_add_g)); fg_step_b=$((fg_step_b-fg_add_b))
			pid_step_r=$((pid_step_r-pid_add_r)); pid_step_g=$((pid_step_g-pid_add_g)); pid_step_b=$((pid_step_b-pid_add_b))
		elif ((current_num>=proc[selected])); then
			fg_step_r=$((fg_step_r+fg_add_r)); fg_step_g=$((fg_step_g+fg_add_g)); fg_step_b=$((fg_step_b+fg_add_b))
			pid_step_r=$((pid_step_r+pid_add_r)); pid_step_g=$((pid_step_g+pid_add_g)); pid_step_b=$((pid_step_b+pid_add_b))
		fi
			
	done
		print -v proc_out -rs
		while ((y<=height-2)); do 
			print -v proc_out -m $((line+y++)) $((col+1)) -rp $((width-2)) -t " "
		done

	if ((proc[order_change]==1 | proc[filter_change]==1 | resized>0)); then
		unset proc_misc
		proc[order_change]=0
		proc[filter_change]=0
		proc[page_change]=1
		print -v proc_misc -m $line $((col+13)) -fg ${box[processes_color]} -rp $((box[processes_width]-14)) -t "─" -rs

		if ((proc[detailed]==1)); then
			print -v proc_misc -m $((d_line+d_height)) $((d_col+detail_graph_width+2)) -fg ${box[processes_color]} -t "┴" -rs
		fi

		if ((tty_width>100)); then
			reverse_string="-fg ${box[processes_color]} -t ┤ -fg ${theme[hi_fg]}${proc[reverse]:+ -ul} -b -t r -fg ${theme[title]} -t everse -rs -fg ${box[processes_color]} -t ├"
			reverse_pos=9
		fi
		print -v proc_misc -m $line $((col+width-${#proc_sorting}-8-reverse_pos)) -rs ${reverse_string}\
		-fg ${box[processes_color]} -t "┤" -fg ${theme[hi_fg]} -b -t "‹" -fg ${theme[title]} -t " ${proc_sorting} "  -fg ${theme[hi_fg]} -t "›" -rs -fg ${box[processes_color]} -t "├"
		
		if [[ -z $filter && -z $input_to_filter ]]; then
			print -v proc_misc -m $line $((col+14)) -fg ${box[processes_color]} -t "┤" -fg ${theme[hi_fg]} -b -t "f" -fg ${theme[title]} -t "ilter" -rs -fg ${box[processes_color]} -t "├"
		elif [[ -n $input_to_filter ]]; then
			if [[ ${#filter} -le $((width-35-reverse_pos)) ]]; then filter_string="${filter}"
			elif [[ ${#filter} -gt $((width-35-reverse_pos)) ]]; then filter_string="${filter: (-$((width-35-reverse_pos)))}"
			fi
			print -v proc_misc -m $line $((col+14)) -fg ${box[processes_color]} -t "┤" -fg ${theme[title]} -b -t "${filter_string}" -fg ${theme[proc_misc]} -bl -t "█" -rs -fg ${box[processes_color]} -t "├"
		elif [[ -n $filter ]]; then
			if [[ ${#filter} -le $((width-35-reverse_pos-4)) ]]; then filter_string="${filter}"
			elif [[ ${#filter} -gt $((width-35-reverse_pos-4)) ]]; then filter_string="${filter::$((width-35-reverse_pos-4))}"
			fi
			print -v proc_misc -m $line $((col+14)) -fg ${box[processes_color]} -t "┤" -fg ${theme[hi_fg]} -b -t "f" -fg ${theme[title]} -t " ${filter_string} " -fg ${theme[hi_fg]} -t "c" -rs -fg ${box[processes_color]} -t "├"
		fi

		
	
		proc_out+="${proc_misc}"
	fi

	if ((proc[page_change]==1 | resized>0)); then
		unset proc_misc2
		proc[page_change]=0
		if ((proc[selected]>0)); then up_fg="${theme[hi_fg]}"; kill_fg="${theme[hi_fg]}"; com_fg="${theme[title]}"; else up_fg="${theme[inactive_fg]}"; kill_fg="${theme[inactive_fg]}"; com_fg="${theme[inactive_fg]}"; fi
		if ((proc[selected]==${#proc_array[@]}-proc_start)); then down_fg="${theme[inactive_fg]}"; else down_fg="${theme[hi_fg]}"; fi

		if ((proc[page]>1)); then page_up_fg="${theme[title]}"; pg_arrow_up_fg="${theme[hi_fg]}"; else page_up_fg="${theme[inactive_fg]}"; pg_arrow_up_fg="${theme[inactive_fg]}"; fi
		if ((proc[page]<proc[pages])); then page_down_fg="${theme[title]}"; pg_arrow_down_fg="${theme[hi_fg]}" ; else page_down_fg="${theme[inactive_fg]}"; pg_arrow_down_fg="${theme[inactive_fg]}"; fi
		page_string="${proc[page]}/${proc[pages]}"
		print -v proc_misc2 -m $((line+height-1)) $((col+width-20)) -fg ${box[processes_color]} -rp 19 -t "─"
		print -v proc_misc2 -m $((line+height-1)) $((col+width-${#page_string}-12)) -fg ${box[processes_color]} -t "┤" -b -fg $page_up_fg -t "pg" -fg $pg_arrow_up_fg "↑" -fg ${theme[title]} -t " $page_string " -fg $page_down_fg -t "pg" -fg $pg_arrow_down_fg "↓" -rs -fg ${box[processes_color]} -t "├"

		print -v proc_misc2 -m $((line+height-1)) $((col+2)) -fg ${box[processes_color]} -t "┤" -fg $up_fg -b -t "↑" -fg ${theme[title]} -t " select " -fg $down_fg -t "↓" -rs -fg ${box[processes_color]} -t "├"
		print -v proc_misc2 -r 1 -fg ${box[processes_color]} -t "┤" -fg $com_fg -b -t "info " -fg $kill_fg "↲" -rs -fg ${box[processes_color]} -t "├"
		if ((tty_width>100)); then print -v proc_misc2 -r 1 -t "┤" -fg $kill_fg -b -t "t" -fg $com_fg -t "erminate" -rs -fg ${box[processes_color]} -t "├"; fi
		if ((tty_width>111)); then print -v proc_misc2 -r 1 -t "┤" -fg $kill_fg -b -t "k" -fg $com_fg -t "ill" -rs -fg ${box[processes_color]} -t "├"; fi
		if ((tty_width>126)); then print -v proc_misc2 -r 1 -t "┤" -fg $kill_fg -b -t "i" -fg $com_fg -t "nterrupt" -rs -fg ${box[processes_color]} -t "├"; fi

		proc_out+="${proc_misc2}"
	fi

	proc_out="${detail_graph[*]}${proc_out}"

	if ((resized>0)); then ((resized++)); fi

	if [[ $argument == "now" ]]; then
		echo -en "${proc_out}"
	fi

}

draw_net() { #? Draw net information and graphs to screen
	local net_out
	#* Get variables from previous calculations
	local col=$((box[net_col]+1)) line=$((box[net_line]+1)) width=$((box[net_width]-2)) height=$((box[net_height]-2))
	local n_width=${box[n_width]} n_height=${box[n_height]} n_col=${box[n_col]} n_line=${box[n_line]} main_fg="${theme[main_fg]}"
	
	#* If resized recreate net meter box and net graphs
	if ((resized>0)); then
		local graph_a_size graph_b_size
		graph_a_size=$(( (height)/2 )); graph_b_size=${graph_a_size}
		if ((graph_a_size*2<height)); then ((graph_a_size++)); fi
		net[graph_a_size]=$graph_a_size
		net[graph_b_size]=$graph_b_size

		create_graph -o download_graph -d $line $col $graph_a_size $((width-n_width-2)) -c color_download_graph -n -max "${net[download_graph_max]}" net_history_download
		create_graph -o upload_graph -d $((line+graph_a_size)) $col $graph_b_size $((width-n_width-2)) -c color_upload_graph -i -n -max "${net[upload_graph_max]}" net_history_upload

		net[download_redraw]=0 
		net[upload_redraw]=0
		((resized++))
	fi
	
	#* Update graphs if graph resolution update is needed or just resized, otherwise just add new values
	if ((net[download_redraw]==1 | resized>0)); then
		create_graph -o download_graph -d $line $col ${net[graph_a_size]} $((width-n_width-2)) -c color_download_graph -n -max "${net[download_graph_max]}" net_history_download
	else
		create_graph -max "${net[download_graph_max]}" -add-last download_graph net_history_download
	fi
	if ((net[upload_redraw]==1 | resized>0)); then
		create_graph -o upload_graph -d $((line+net[graph_a_size])) $col ${net[graph_b_size]} $((width-n_width-2)) -c color_upload_graph -i -n -max "${net[upload_graph_max]}" net_history_upload
	else
		create_graph -max "${net[upload_graph_max]}" -i -add-last upload_graph net_history_upload
	fi

	#* Create text depening on box height
	local ypos=$n_line

	print -v net_out -fg ${main_fg} -m $((ypos++)) $n_col -jl 10 -t "▼ Byte:" -jr 12 -t "${net[speed_download_byteps]}"
	if ((height>4)); then print -v net_out -fg ${main_fg} -m $((ypos++)) $n_col -jl 10 -t "▼ Bit:" -jr 12 -t "${net[speed_download_bitps]}"; fi
	if ((height>6)); then print -v net_out -fg ${main_fg} -m $((ypos++)) $n_col -jl 10 -t "▼ Total:" -jr 12 -t "${net[total_download]}"; fi
	
	if ((height>8)); then ((ypos++)); fi
	print -v net_out -fg ${main_fg} -m $((ypos++)) $n_col -jl 10 -t "▲ Byte:" -jr 12 -t "${net[speed_upload_byteps]}"
	if ((height>7)); then print -v net_out -fg ${main_fg} -m $((ypos++)) $n_col -jl 10 -t "▲ Bit:" -jr 12 -t "${net[speed_upload_bitps]}"; fi
	if ((height>5)); then print -v net_out -fg ${main_fg} -m $((ypos++)) $n_col -jl 10 -t "▲ Total:" -jr 12 -t "${net[total_upload]}"; fi
	

	#* Print graphs and text to output variable
	draw_out+="${download_graph[*]}${upload_graph[*]}${net_out}"
}

draw_clock() { #? Draw a clock at top of screen
	if [[ -z $draw_clock ]]; then return; fi
	if [[ $resized -gt 0 && $resized -lt 5 ]]; then unset clock_out; return; fi
	local width=${box[cpu_width]} color=${box[cpu_color]} old_time_string="${time_string}"
	#time_string="$(date ${draw_clock})"
	printf -v time_string "%(${draw_clock})T"
	if [[ $old_time_string != "$time_string" || -z $clock_out ]]; then
		unset clock_out
		print -v clock_out -m 1 $((width/2-${#time_string}/2)) -rs -fg ${color} -t "┤" -fg ${theme[title]} -b -t "${time_string}" -fg ${color} -t "├"
	fi
	if [[ $1 == "now" ]]; then echo -en "${clock_out}"; fi
}

draw_update_string() {
	unset update_string
	print -v update_string -m ${box[cpu_line]} $((box[cpu_col]+box[cpu_width]-${#update_ms}-14)) -rs -fg ${box[cpu_color]} -t "────┤"  -fg ${theme[hi_fg]} -b -t "+" -fg ${theme[title]} -b -t " ${update_ms}ms "  -fg ${theme[hi_fg]} -b -t "-" -rs -fg ${box[cpu_color]} -t "├"
	if [[ $1 == "quiet" ]]; then draw_out+="${update_string}"
	else echo -en "${update_string}"; fi
}

pause_() { #? Pause input and draw a darkened version of main ui
	local pause_out ext_var
	if [[ -n $1 && $1 != "off" ]]; then local -n pause_out=${1}; ext_var=1; fi
	if [[ $1 != "off" ]]; then
		prev_screen="${boxes_out}${proc_det}${last_screen}${mem_out}${detail_graph[*]}${proc_out}${proc_misc}${proc_misc2}${update_string}${clock_out}"
		if [[ -n $skip_process_draw ]]; then
			prev_screen+="${proc_out}"
			unset skip_process_draw proc_out
		fi
		
		unset pause_screen
		print -v pause_screen -rs -b -fg ${theme[inactive_fg]}
		pause_screen+="${theme[main_bg]}m$(sed -E 's/\\e\[[0-9;\-]*m//g' <<< "${prev_screen}")\e[0m" #\e[1;38;5;236
		
		if [[ -z $ext_var ]]; then echo -en "${pause_screen}"
		else pause_out="${pause_screen}"; fi

	elif [[ $1 == "off" ]]; then
		echo -en "${prev_screen}"
		unset pause_screen prev_screen
	fi
}

unpause_() { #? Unpause
	pause_ off
}

menu_() { #? Shows the main menu overlay
	local menu i count keypress selected_int=0 selected up local_rez d_banner=1 menu_out bannerd skipped menu_pause out_out wait_string trans
	local -a menus=("options" "help" "quit") color
	
	until false; do

		#* Put program to sleep if caught ctrl-z
		if ((sleepy==1)); then sleep_; fi

		if [[ $background_update == true || -z $menu_out ]]; then
			draw_clock
			pause_ menu_pause
		else
			unset menu_pause
		fi

		unset draw_out

		if [[ -z ${bannerd} ]]; then
			draw_banner "$((tty_height/2-10))" bannerd
			unset d_banner
		fi
		if [[ -n ${keypress} || -z ${menu_out} ]]; then
			unset menu_out
			print -v menu_out -t "${bannerd}"
			print -v menu_out -d 1 -rs
			selected="${menus[selected_int]}"
			unset up
			if [[ -n ${theme[main_bg_dec]} ]] && ((${theme[main_bg_dec]// /*}>255**3/2)); then print -v menu_out -bg "#00"; unset trans; else trans=" -trans"; fi
			for menu in "${menus[@]}"; do
				if [[ $menu == "$selected" ]]; then
					local -n menu_array="menu_${menu}_selected"
					color=("#c55e5e" "#c23d3d" "#a13030" "#8c2626")
				else
					local -n menu_array="menu_${menu}"
					color=("#bb" "#aa" "#99" "#88")
				fi
				up=$((up+${#menu_array[@]}))
				for((i=0;i<${#menu_array[@]};i++)); do
					print -v menu_out -d 1 -fg ${color[i]} -c${trans} -t "${menu_array[i]}"
				done
			done
			print -v menu_out -rs -u ${up}
		fi
		unset out_out
		out_out="${menu_pause}${menu_out}"
		echo -e "${out_out}"
		
		
		get_ms timestamp_end
		time_left=$((timestamp_start+update_ms-timestamp_end))
		if ((time_left>1000)); then wait_string=1; time_left=$((time_left-1000))
		elif ((time_left>1)); then printf -v wait_string ".%03d" "${time_left}"; time_left=0
		else wait_string="0.001"; time_left=0; fi
		
		get_key -v keypress -w ${wait_string}
		if [[ $(stty size) != "$tty_height $tty_width" ]]; then resized; fi
		if ((resized>0)); then 
			calc_sizes; draw_bg quiet; time_left=0; unset menu_out
			unset bannerd
		fi

		case "$keypress" in
			up|shift_tab) if ((selected_int>0)); then ((selected_int--)); else selected_int=$((${#menus[@]}-1)); fi ;;
			down|tab) if ((selected_int<${#menus[@]}-1)); then ((++selected_int)); else selected_int=0; fi ;;
			enter|space)
				case "$selected" in
					options) options_ ;;
					help) help_ ;;
					quit) quit_ ;;
				esac
			;;
			m|M|escape|backspace) break ;;
			q|Q) quit_ ;;
		esac
		
		if ((time_left==0)); then get_ms timestamp_start; collect_and_draw; fi
		if ((resized>=5)); then resized=0; fi

	done				
	unpause_
	
}

help_() { #? Shows the help overlay
	local tmp from_menu col line y i help_out help_pause redraw=1 wait_string
	local -a shortcuts descriptions

	shortcuts=(
		"(Esc, M, m)"
		"(F2, O, o)"
		"(F1, H, h)"
		"(Ctrl-C, Q, q)"
		"(+, A, a) (-, S, s)"
		"(Up) (Down)"
		"(Enter)"
		"(Pg Up) (Pg Down)"
		"(Home) (End)"
		"(Left, Right)"
		"(R, r)"
		"(F, f)"
		"(C, c)"
		"(T, t)"
		"(K, k)"
		"(I, i)"
	)
	descriptions=(
		"Shows main menu."
		"Shows options."
		"Shows this window."
		"Quits program."
		"Add/Subtract 100ms to/from update timer."
		"Select in process list."
		"Show detailed information for selected process."
		"Jump 1 page in process list."
		"Jump to first or last page in process list."
		"Select previous/next sorting column."
		"Reverse sorting order in processes box."
		"Input a string to filter processes with."
		"Clear any entered filter."
		"Terminate selected process with SIGTERM - 15."
		"Kill selected process with SIGKILL - 9."
		"Interrupt selected process with SIGINT - 2."
	)

	if [[ -n $pause_screen ]]; then from_menu=1; fi
	
	until [[ -n $tmp ]]; do

		#* Put program to sleep if caught ctrl-z
		if ((sleepy==1)); then sleep_; redraw=1; fi

		if [[ $background_update == true || -n $redraw ]]; then
			draw_clock
			pause_ help_pause
		else
			unset help_pause
		fi


		if [[ -n $redraw ]]; then
			col=$((tty_width/2-36)); line=$((tty_height/2-4)); y=1
			unset redraw help_out
			draw_banner "$((tty_height/2-11))" help_out
			print -d 1
			create_box -v help_out -w 72 -h $((${#shortcuts[@]}+3)) -l $((line++)) -c $((col++)) -fill -lc ${theme[div_line]} -title "help"
			((++col))

			print -v help_out -r 1 -fg ${theme[title]} -b -jl 20 -t "Key:" -jl 48 -t "Description:" -m $((line+y++)) $col
			
			for((i=0;i<${#shortcuts[@]};i++)); do
				print -v help_out -fg ${theme[main_fg]} -b -jl 20 -t "${shortcuts[i]}" -rs -fg ${theme[main_fg]} -jl 48 -t "${descriptions[i]}" -m $((line+y++)) $col
			done
		fi


		unset draw_out
		echo -en "${help_pause}${help_out}"
		
		get_ms timestamp_end
		time_left=$((timestamp_start+update_ms-timestamp_end))
		
		if ((time_left>1000)); then wait_string=1; time_left=$((time_left-1000))
		elif ((time_left>0)); then printf -v wait_string ".%03d" "${time_left}"; time_left=0
		else wait_string="0.001"; time_left=0; fi
		
		get_key -v tmp -w "${wait_string}"
		if [[ $(stty size) != "$tty_height $tty_width" ]]; then resized; fi
		if ((resized>0)); then 
			sleep 0.5
			calc_sizes; draw_bg quiet; redraw=1
			d_banner=1
			unset bannerd menu_out
		fi
		if ((time_left==0)); then get_ms timestamp_start; collect_and_draw; fi
		if ((resized>0)); then resized=0; fi
	done

	if [[ -n $from_menu ]]; then pause_
	else unpause_; fi
}

options_() { #? Shows the options overlay
	local keypress from_menu col line y=1 i=1 options_out selected_int=0 ypos option_string options_misc option_value bg fg skipped start_t end_t left_t changed_cpu_name theme_int=0
	local desc_col right left enter lr inp valid updated_ms local_rez redraw_misc=1 desc_pos desc_height options_pause updated_proc inputting inputting_value inputting_key file theme_check

	#* Check theme folder for theme files
	get_themes

	desc_color_theme=(	"Set bashtop color theme."
						" "
						"Choose between theme files located in"
						"\"\$HOME/.config/bashtop/themes\""
						" "
						"\"Default\" for builtin default."
						" ")
	if [[ -z $curled ]]; then desc_color_theme+=("Get more themes at:"
						"https://github.com/aristocratos/bashtop")
	else desc_color_theme+=("\e[1mPress ENTER to check for new themes."); fi

	desc_update_ms=(	"Update time in milliseconds."
						"Recommended 2000 ms or above for better sample"
						"times for graphs."
						" "
						"Increases automatically if set below internal"
						"loops processing time."
						" "
						"Max value: 86400000 ms = 24 hours.")
	desc_proc_sorting=(	"Processes sorting."
						"Valid values are \"pid\", \"program\", \"arguments\","
						"\"threads\", \"user\", \"memory\", \"cpu lazy\" and"
						"\"cpu responsive\"."
						" "
						"\"cpu lazy\" uses ps commands internal sorting"
						"and updates top process over a period of time."
						" "
						"\"cpu responsive\" updates sorting directly at a"
						"cost of cpu time.")
	desc_check_temp=(	"Check cpu temperature."
						" "
						"Only works if sensors command is available"
						"and show values for Package and Core"
						"temperatures.")
	desc_draw_clock=(	"Draw a clock at top of screen."
						" "
						"Formatting according to strftime, empty"
						"string to disable."
						" "
						"\"%X\" locale HH:MM:SS"
						"\"%H\" 24h hour, \"%I\" 12h hour"
						"\"%M\" minute, \"%S\" second"
						"\"%d\" day, \"%m\" month, \"%y\" year")
	desc_background_update=( "Update main ui when menus are showing."
							" "
							"True or false."
							" "
							"Set this to false if the menus is flickering"
							"too much for a comfortable experience.")
	desc_custom_cpu_name=(	"Custom cpu model name in cpu percentage box."
							" "
							"Empty string to disable.")
	desc_error_logging=("Enable error logging to"
						"\"\$HOME/.config/bashtop/error.log\""
						" "
						"True or false."
						"Takes effect after program restart.")
	

	if [[ -n $pause_screen ]]; then from_menu=1; fi

	until false; do

		#* Put program to sleep if caught ctrl-z
		if ((sleepy==1)); then sleep_; fi
		
		
		if [[ $background_update == true || -n $redraw_misc ]]; then
			draw_clock
			pause_ options_pause
		else
			unset options_pause
		fi

		if [[ -n $redraw_misc ]]; then
			unset options_misc redraw_misc
			col=$((tty_width/2-39))
			line=$((tty_height/2-4))
			desc_col=$((col+30))
			draw_banner "$((tty_height/2-11))" options_misc
			create_box -v options_misc -w 29 -h $((${#options_array[@]}*2+2)) -l $line -c $((col-1)) -fill -lc ${theme[div_line]} -title "options"
		fi
		
		
		if [[ -n $keypress || -z $options_out ]]; then
			unset options_out desc_height lr inp valid
			selected="${options_array[selected_int]}"
			local -n selected_desc="desc_${selected}"
			if [[ $background_update == false ]]; then desc_pos=$line; desc_height=$((${#options_array[@]}*2+2))
			elif ((selected_int*2+${#selected_desc[@]}<${#options_array[@]}*2)); then desc_pos=$((line+selected_int*2))
			else desc_pos=$((line+${#options_array[@]}*2-${#selected_desc[@]})); fi
			create_box -v options_out -w 50 -h ${desc_height:-$((${#selected_desc[@]}+2))} -l $desc_pos -c $((desc_col-1)) -fill -lc ${theme[div_line]} -title "description"
			for((i=0,ypos=1;i<${#options_array[@]};i++,ypos=ypos+2)); do
				option_string="${options_array[i]}"
				if [[ -n $inputting && ${option_string} == "${selected}" ]]; then 
					if [[ ${#inputting_value} -gt 14 ]]; then option_value="${inputting_value:(-14)}_"
					else option_value="${inputting_value}_"; fi
				else 
					option_value="${!option_string}"
				fi
				
				if [[ ${option_string} == "${selected}" ]]; then
					if is_int "$option_value" || [[ $selected == "color_theme" && -n $curled ]]; then
						enter="↲"; inp=1
					fi
					if is_int "$option_value" || [[ $option_value =~ true|false || $selected =~ proc_sorting|color_theme ]] && [[ -z $inputting ]]; then
						left="←"; right="→"; lr=1
					else
						enter="↲"; inp=1
					fi
					bg=" -bg ${theme[selected_bg]}"
					fg="${theme[selected_fg]}"
				fi
				option_string="${option_string//_/ }:"
				if [[ $option_string == "proc sorting:" ]]; then option_string+=" $((proc[sorting_int]+1))/${#sorting[@]}"
				elif [[ $option_string == "color theme:" ]]; then option_string+=" $((theme_int+1))/${#themes[@]}"; fi
				print -v options_out -m $((line+ypos)) $((col+1)) -rs -fg ${fg:-${theme[title]}}${bg} -b -jc 25 -t "${option_string^}"
				print -v options_out -m $((line+ypos+1)) $((col+1)) -rs -fg ${fg:-${theme[main_fg]}}${bg} -jc 25 -t "${enter:+ } ${left} \"${option_value::15}\" ${right} ${enter}"
				unset right left enter bg fg
			done

			for((i=0,ypos=1;i<${#selected_desc[@]};i++,ypos++)); do
				print -v options_out -m $((desc_pos+ypos)) $((desc_col+1)) -rs -fg ${theme[main_fg]} -jl 46 -t "${selected_desc[i]}"
			done
		fi

		echo -en "${options_pause}${options_misc}${options_out}"
		unset draw_out keypress

		if [[ -n $theme_check ]]; then
			local -a theme_index
			local git_theme new_themes=0
			unset 'theme_index[@]' 'desc_color_theme[-1]' options_out
			theme_index=($(curl -m 3 --raw https://raw.githubusercontent.com/aristocratos/bashtop/master/themes/index.txt 2>/dev/null))
			if [[ ${theme_index[*]} =~ .theme ]]; then
				for git_theme in ${theme_index[@]}; do
					if [[ $git_theme =~ .theme && ! -e "${theme_dir}/${git_theme}" ]]; then
						if curl -m 3 --raw "https://raw.githubusercontent.com/aristocratos/bashtop/master/themes/${git_theme}" >"${theme_dir}/${git_theme}" 2>/dev/null; then
							((++new_themes))
							themes+=("${git_theme%.theme}")
						fi
					fi
				done
				desc_color_theme+=("Found ${new_themes} new theme(s)!")
			else
				desc_color_theme+=("ERROR: Couldn't get theme index!")
			fi
		fi
		
		
		get_ms timestamp_end
		if [[ -z $theme_check ]]; then time_left=$((timestamp_start+update_ms-timestamp_end))
		else unset theme_check; time_left=0; fi
		if ((time_left>500)); then wait_string=0.5
		elif ((time_left>0)); then printf -v wait_string ".%03d" "${time_left}"
		else wait_string="0.001"; time_left=0; fi
				
		get_key -v keypress -w ${wait_string}
		
		if [[ -n $inputting ]]; then
			case "$keypress" in
				escape) unset inputting inputting_value ;;
				enter|backspace) valid=1 ;;
				*) if [[ ${#keypress} -eq 1 ]]; then valid=1; fi ;;
			esac
		else
			case "$keypress" in
				escape|q|backspace) break 1 ;;
				down|tab) if ((selected_int<${#options_array[@]}-1)); then ((++selected_int)); else selected_int=0; fi ;;
				up|shift_tab) if ((selected_int>0)); then ((selected_int--)); else selected_int=$((${#options_array[@]}-1)); fi ;;
				left|right) if [[ -n $lr && -z $inputting ]]; then valid=1; fi ;;
				enter) if [[ -n $inp ]]; then valid=1; fi ;;
			esac
		fi
	
		if [[ ${selected} == "color_theme" && ${keypress} =~ left|right && ${#themes} -lt 2 ]]; then unset valid; fi

		if [[ -n $valid ]]; then
			case "${selected} ${keypress}" in
				"update_ms right") 
						if ((update_ms<86399900)); then
							update_ms=$((update_ms+100))
							updated_ms=1
						fi
					;;
				"update_ms left")
						if ((update_ms>100)); then
							update_ms=$((update_ms-100))
							updated_ms=1
						fi
					;;
				"update_ms enter")
						if [[ -z $inputting ]]; then inputting=1; inputting_value="${update_ms}"
						else 
							if ((inputting_value<86400000)); then update_ms="${inputting_value:-0}"; updated_ms=1; fi
							unset inputting inputting_value
						fi
					;;
				"update_ms backspace"|"draw_clock backspace"|"custom_cpu_name backspace")
						if [[ ${#inputting_value} -gt 0 ]]; then
							inputting_value="${inputting_value::-1}"
						fi
					;;
				"update_ms"*)
						inputting_value+="${keypress//[^0-9]/}"
					;;
				"draw_clock enter")
						if [[ -z $inputting ]]; then inputting=1; inputting_value="${draw_clock}"
						else draw_clock="${inputting_value}"; unset inputting inputting_value clock_out; fi
					;;
				"custom_cpu_name enter")
						if [[ -z $inputting ]]; then inputting=1; inputting_value="${custom_cpu_name}"
						else custom_cpu_name="${inputting_value}"; changed_cpu_name=1; unset inputting inputting_value; fi
					;;	
				"check_temp"*|"error_logging"*|"background_update"*)
						local -n selected_var=${selected}
						if [[ ${selected_var} == "true" ]]; then
							selected_var="false"
							if [[ $selected == "proc_reversed" ]]; then proc[order_change]=1; unset 'proc[reverse]'; fi
						else
							selected_var="true"
							if [[ $selected == "proc_reversed" ]]; then proc[order_change]=1; proc[reverse]="+"; fi
						fi
						if [[ $selected == "check_temp" ]]; then resized=1; fi
					;;
				"proc_sorting right")
						if ((proc[sorting_int]<${#sorting[@]}-1)); then ((++proc[sorting_int]))
						else proc[sorting_int]=0; fi
						proc_sorting="${sorting[proc[sorting_int]]}"
						proc[order_change]=1
					;;
				"proc_sorting left")
						if ((proc[sorting_int]>0)); then ((proc[sorting_int]--))
						else proc[sorting_int]=$((${#sorting[@]}-1)); fi
						proc_sorting="${sorting[proc[sorting_int]]}"
						proc[order_change]=1
					;;
				"color_theme right")
						if ((theme_int<${#themes[@]}-1)); then ((++theme_int))
						else theme_int=0; fi
						color_theme="${themes[$theme_int]}"
						color_init_
						resized=1
					;;
				"color_theme left")
						if ((theme_int>0)); then ((theme_int--))
						else theme_int=$((${#themes[@]}-1)); fi
						color_theme="${themes[$theme_int]}"
						color_init_
						resized=1
					;;
				"color_theme enter")
						theme_check=1
						if ((${#desc_color_theme[@]}>8)); then unset 'desc_color_theme[-1]'; fi
						desc_color_theme+=("Checking for new themes...")
					;;
				"draw_clock"*|"custom_cpu_name"*)
						inputting_value+="${keypress//[\\\$\"\']/}"
					;;
			esac

		fi

		if [[ -n $changed_cpu_name ]]; then
			changed_cpu_name=0
			get_cpu_info
			calc_sizes
			draw_bg quiet
		fi

		if [[ $(stty size) != "$tty_height $tty_width" ]]; then resized; fi

		if ((resized>0)); then 
			calc_sizes; draw_bg quiet
			redraw_misc=1
			unset options_out bannerd menu_out
		fi

		get_ms timestamp_end
		time_left=$((timestamp_start+update_ms-timestamp_end))
		if ((time_left<=0 | resized>0)); then get_ms timestamp_start; collect_and_draw; fi
		if ((resized>0)); then resized=0; fi

		if [[ -n $updated_ms ]] && ((updated_ms++==2)); then
			unset updated_ms
			draw_update_string quiet
		fi

	done

	if [[ -n $from_menu ]]; then pause_
	elif [[ -n ${pause_screen} ]]; then unpause_; draw_update_string; fi
}

killer_() { #? Kill process with selected signal
	local kill_op="$1" kill_pid="$2" killer_out killer_box col line program keypress selected selected_int=0 sig confirmed=0 option killer_pause status msg
	local -a options=("yes" "no")
	
	if ! program="$(ps -o comm --no-header -p ${kill_pid})"; then return; fi

	case $kill_op in
		t|T) kill_op="terminate"; sig="SIGTERM" ;;
		k|K) kill_op="kill"; sig="SIGKILL" ;;
		i|I) kill_op="interrupt"; sig="SIGINT" ;;
	esac
	
	until false; do

		#* Put program to sleep if caught ctrl-z
		if ((sleepy==1)); then sleep_; fi

		if [[ $background_update == true || -z $killer_box ]]; then
			draw_clock
			pause_ killer_pause
		else
			unset killer_pause
		fi

		if [[ -z $killer_box ]]; then
			col=$((tty_width/2-15)); line=$((tty_height/2-4)); y=1
			unset redraw killer_box
			create_box -v killer_box -w 40 -h 9 -l $line -c $((col++)) -fill -lc "${theme[proc_box]}" -title "${kill_op}"	
		fi

		if ((confirmed==0)); then
			selected="${options[selected_int]}"
			print -v killer_out -m $((line+2)) $col -fg ${theme[title]} -b -jc 38 -t "${kill_op^} ${program::20}?" -m $((line+4)) $((col+3))
			for option in "${options[@]}"; do
				if [[ $option == "${selected}" ]]; then print -v killer_out -bg ${theme[selected_bg]} -fg ${theme[selected_fg]}; else print -v killer_out -fg ${theme[title]}; fi
				print -v killer_out -b -r 5 -t "[  ${option^}  ]" -rs
			done

		elif ((confirmed==1)); then
			selected="ok"
			print -v killer_out -m $((line+2)) $col -fg ${theme[title]} -b -jc 38 -t "Sending signal ${sig} to pid ${kill_pid}!"
			print -v killer_out -m $((line+4)) $col -fg ${theme[main_fg]} -jc 38 -t "${status^}!" -m $((line+6)) $col
			if [[ -n $msg ]]; then print -v killer_out -m $((line+5)) $col -fg ${theme[main_fg]} -jc 38 -t "${msg}" -m $((line+7)) $col; fi
			print -v killer_out -fg ${theme[selected_fg]} -bg ${theme[selected_bg]} -b -r 15 -t "[  Ok  ]" -rs
		fi
	
		echo -en "${killer_pause}${killer_box}${killer_out}"
		unset killer_out draw_out
		
		
		get_ms timestamp_end
		time_left=$((timestamp_start+update_ms-timestamp_end))
		if ((time_left>1000)); then wait_string=1; time_left=$((time_left-1000))
		elif ((time_left>1)); then printf -v wait_string ".%03d" "${time_left}"; time_left=0
		else wait_string="0.001"; time_left=0; fi
		
		get_key -v keypress -w ${wait_string}
		if [[ $(stty size) != "$tty_height $tty_width" ]]; then resized; fi
		if ((resized>0)); then 
			calc_sizes; draw_bg quiet; time_left=0; unset killer_out killer_box
		fi

		case "$keypress" in
			right|shift_tab) if ((selected_int>0)); then ((selected_int--)); else selected_int=$((${#options[@]}-1)); fi ;;
			left|tab) if ((selected_int<${#options[@]}-1)); then ((++selected_int)); else selected_int=0; fi ;;
			enter)
				case "$selected" in
					yes) confirmed=1 ;;
					no|ok) confirmed=-1 ;;
				esac
			;;
			q|Q) quit_ ;;
		esac
		
		

		if ((confirmed<0)); then
			unpause_
			break
		elif ((confirmed>0)) && [[ -z $status ]]; then
			if kill -${sig} ${kill_pid} >/dev/null 2>&1; then 
				status="success"
			else 
				if ! ps -p ${kill_pid} >/dev/null 2>&1; then
					msg="Process not running."
				elif [[ $UID != 0 ]]; then
					msg="Try restarting with sudo."
				else
					msg="Unknown error."
				fi
				status="failed"; fi
		fi
				

		if ((time_left==0)); then get_ms timestamp_start; unset draw_out; collect_and_draw; fi
		if ((resized>=5)); then resized=0; fi

	done				
	
	
}

get_key() { #? Get one key from standard input and translate key code to readable format
	local key key_out wait_time esc ext_out save

	if ((quitting==1)); then quit_; fi

	until (($#==0)); do
		case "$1" in
			-v|-variable) local -n key_out=$2; ext_out=1; shift;;			#* Output variable
			-w|-wait) wait_time="$2"; shift;;								#* Time to wait for key
			-s|-save) save=1;;												#* Save key for later processing
		esac
		shift
	done
		
	if [[ -z $save && -n ${saved_key[0]} ]]; then key="${saved_key[0]}"; unset 'saved_key[0]'; saved_key=("${saved_key[@]}")
	else
		unset key
		IFS= read -rsd '' -t ${wait_time:-0.001} -n 1 key >/dev/null 2>&1 ||true

		if [[ -z ${key:+s} ]]; then 
			key_out=""
			if [[ -z $save ]]; then return 0
			else return 1; fi
		fi
		
		#* Read 3 more characters if a leading escape character is detected
		if [[ $key == "${enter_key}" ]]; then key="enter"
		elif [[ $key == "${backspace}" ]]; then key="backspace"
		elif [[ $key == "${tab}" ]]; then key="tab"
		elif [[ $key == "$esc_character" ]]; then esc=1; read -rsn3 -t 0.0001 key || true; fi
		if [[ -z $key && $esc -eq 1 ]]; then key="escape"
		elif [[ $esc -eq 1 ]]; then
			case "${key}" in
				'[A') key="up" ;;
				'[B') key="down" ;;
				'[D') key="left" ;;
				'[C') key="right" ;;
				'[2~') key="insert" ;;
				'[3~') key="delete" ;;
				'[H') key="home" ;;
				'[F') key="end" ;;
				'[5~') key="page_up" ;;
				'[6~') key="page_down" ;;
				'[Z') key="shift_tab" ;;
				'OP') key="f1";;
				'OQ') key="f2";;
				'OR') key="f3";;
				'OS') key="f4";;
				'[15') key="f5";;
				'[17') key="f6";;
				'[18') key="f7";;
				'[19') key="f8";;
				'[20') key="f9";;
				'[21') key="f10";;
				'[23') key="f11";;
				'[24') key="f12";;
				*) key="" ;;
			esac
		fi

	fi

	read -rst 0.0001 -n 1000 2>/dev/null ||true
	
	if [[ -n $save && -n $key ]]; then saved_key+=("${key}"); return 0; fi

	if [[ -n $ext_out ]]; then key_out="${key}"
	else echo -n "${key}"; fi
}

process_input() { #? Process keypresses for main ui
	local wait_time="$1" keypress esc prev_screen anykey filter_change
	late_update=0
	#* Wait while reading input
	get_key -v keypress -w "${wait_time}"
	if [[ -z $keypress ]]; then return; fi

	if [[ -n $input_to_filter ]]; then
		filter_change=1
		case "$keypress" in
			"enter") unset input_to_filter ;;
			"backspace") if [[ ${#filter} -gt 0 ]]; then filter="${filter:: (-1)}"; else unset filter_change; fi ;;
			"escape") unset input_to_filter filter ;;
			*) if [[ ${#keypress} -eq 1 ]]; then filter+="${keypress//[\\\$\"\']/}"; else unset filter_change; fi ;;
		esac
			
	else
		case "$keypress" in
			left) #* Move left in processes sorting column
				if ((proc[sorting_int]>0)); then ((proc[sorting_int]--))
				else proc[sorting_int]=$((${#sorting[@]}-1)); fi
				proc_sorting="${sorting[proc[sorting_int]]}"
				filter_change=1
			;;
			right) #* Move right in processes sorting column
				if ((proc[sorting_int]<${#sorting[@]}-1)); then ((++proc[sorting_int]))
				else proc[sorting_int]=0; fi
				proc_sorting="${sorting[proc[sorting_int]]}"
				filter_change=1
			;;
			up|shift_tab) #* Move process selector up one
				if [[ ${proc[selected]} -gt 0 ]]; then
					((proc[selected]--))
					if ((proc[page]>1 & proc[selected]==0)); then ((--proc[page])); proc[selected]=$((box[processes_height]-3)); fi
					proc[page_change]=1
				fi
			;;
			down|tab) #* Move process selector down one
				if ! ((proc[page]==proc[pages] & proc[selected]>=box[processes_height]-3)); then
					if ((++proc[selected]==1)); then collect_processes now; proc[detailed_change]=1; fi
					if ((proc[selected]>box[processes_height]-3)); then ((proc[page]++)); proc[selected]=1; fi
					proc[page_change]=1
				fi
			;;
			enter) #* Show detailed info for selected process or close detailed info if no new process is selected
				if ((proc[selected]>0 & proc[detailed_pid]!=proc[selected_pid])) && ps -p ${proc[selected_pid]} > /dev/null 2>&1; then
					proc[detailed]=1
					proc[detailed_change]=1
					proc[detailed_pid]=${proc[selected_pid]}
					proc[page]=1
					proc[selected]=0
					unset 'proc[detailed_name]' 'detail_history[@]' 'detail_mem_history[@]' 'proc[detailed_killed]'
					calc_sizes
					collect_processes now
				elif ((proc[detailed]==1 & proc[detailed_pid]!=proc[selected_pid])); then
					proc[detailed]=0
					proc[detailed_change]=1
					unset 'proc[detailed_pid]'
					calc_sizes
				fi
			;;
			page_up) #* Move up one page in process box
				if [[ ${proc[page]} -gt 1 ]]; then
					((--proc[page]))
					proc[page_change]=1
				elif [[ ${proc[selected]} -gt 0 ]]; then
					proc[selected]=0
					proc[page_change]=1
				fi
			;;
			page_down) #* Move down one page in process box
				if [[ ${proc[page]} -lt ${proc[pages]} ]]; then
					if ((proc[page]++==1)); then collect_processes now; fi
					proc[page_change]=1
				elif [[ ${proc[selected]} -gt 0 ]]; then
					proc[selected]=$((box[processes_height]-3))
					proc[page_change]=1
				fi
			;;
			home) #* Go to first page in process box
					proc[page]=1
					proc[page_change]=1
			;;
			end) #* Go to last page in process box
					if ((proc[selected]==0)); then collect_processes now; fi
					proc[page]=${proc[pages]}
					proc[page_change]=1
			;;
			r|R) #* Reverse order of processes sorting column
				if [[ -z ${proc[reverse]} ]]; then
					proc[reverse]="+"
					proc_reversed="true"
				else
					proc_reversed="false"
					unset 'proc[reverse]'
				fi
				filter_change=1
			;;
			o|O|f2) #* Options
				options_
			;;
			+|A|a) #* Add 100ms to update timer
				if ((update_ms<86399900)); then
					update_ms=$((update_ms+100))
					draw_update_string
				fi
			;;
			-|S|s) #* Subtract 100ms from update timer
				if ((update_ms>100)); then
					update_ms=$((update_ms-100))
					draw_update_string
				fi
			;;
			h|H|f1) #* Show help
				help_
			;;
			q|Q) #* Quit
				quit_
			;;
			m|M|escape) #* Show main menu
				menu_
			;;
			f|F) #* Start process filtering input
				input_to_filter=1
				filter_change=1
			;;
			c|C) #* Clear process filter
				if [[ -n $filter ]]; then
					unset input_to_filter filter
					filter_change=1
				fi
			;;
			t|T|k|K|i|I) #* Send terminate, kill or interrupt signal
				if [[ ${proc[selected]} -gt 0 ]]; then
					killer_ "$keypress" "${proc[selected_pid]}"
				elif [[ ${proc[detailed]} -eq 1 && -z ${proc[detailed_killed]} ]]; then
					killer_ "$keypress" "${proc[detailed_pid]}"
				fi
			;;
		esac
	fi

	if [[ -n $filter_change ]]; then
		unset filter_change
		collect_processes now
		proc[filter_change]=1
		draw_processes now
	elif [[ ${proc[page_change]} -eq 1 || ${proc[detailed_change]} == 1 ]]; then
		if ((proc[selected]==0)); then unset 'proc[selected_pid]'; proc[detailed_change]=1; fi
		draw_processes now
	fi

	#* Subtract time since input start from time left if timer is interrupted
	get_ms timestamp_input_end
	time_left=$(( (timestamp_start+update_ms)-timestamp_input_end ))

	return 0
}

collect_and_draw() { #? Run all collect and draw functions
	local task_int=0
	for task in processes cpu mem net; do
		((++task_int))
		if [[ -n $pause_screen && -n ${saved_key[0]} ]]; then 
			return
		elif [[ -z $pause_screen ]]; then
			while [[ -n ${saved_key[0]} ]]; do
				process_input 0.001
				unset late_update
			done
		fi
		collect_${task}
		if get_key -save && [[ -z $pause_screen ]]; then process_input; fi
		draw_${task}
		if get_key -save && [[ -z $pause_screen ]]; then process_input; fi
		draw_clock "$1"
		if ((resized>0 & resized<task_int)); then return; fi
	done

	last_screen="${draw_out}"
}

#? ----------------------------------------------------------------------------------------------------------------------- ?#

main_loop() { #? main loop...
	local wait_time wait_string

	#* Put program to sleep if caught ctrl-z
	if ((sleepy==1)); then sleep_; fi
	
	#* Timestamp for accurate timer
	get_ms timestamp_start

	if [[ $(stty size) != "$tty_height $tty_width" ]]; then resized; fi

	if ((resized>0)); then
		calc_sizes
		draw_bg
	fi

	#* Run all collect and draw functions
	collect_and_draw now

	#* Reset resized variable if resized and all functions have finished redrawing
	if ((resized>=5)); then resized=0
	elif ((resized>0)); then unset draw_out proc_out clock_out; return; fi
	
	#* Echo everyting out to screen in one command to get a smooth transition between updates
	echo -en "${draw_out}${proc_out}${clock_out}"
	unset draw_out
	
	#* Compare timestamps to get exact time needed to wait until next loop
	get_ms timestamp_end
	time_left=$((timestamp_start+update_ms-timestamp_end))
	if ((time_left>0)); then

		late_update=0

		#* Divide waiting time in chunks of 500ms and below to keep program responsive while reading input
		while ((time_left>0 & resized==0)); do

			#* If NOT waiting for input and time left is greater than 500ms, wait 500ms and loop
			if [[ -z $input_to_filter ]] && ((time_left>=500)); then
				wait_string="0.5"
				time_left=$((time_left-500))
			
			#* If waiting for input and time left is greater than "50 ms", wait 50ms and loop
			elif [[ -n $input_to_filter ]] && ((time_left>=50)); then
				wait_string="0.05"
				time_left=$((time_left-50))

			#* Else format wait string with padded zeroes if needed and break loop
			else 
				printf -v wait_string ".%03d" "${time_left}"
				time_left=0
			fi

			#* Wait while reading input
			while [[ -n ${saved_key[0]} ]]; do
				process_input
				late_update=0
			done	
			process_input "${wait_string}"

			#* Draw clock if set	
			draw_clock now

		done

	#* If time left is too low to process any input more than twice in succession, add 100ms to update timer
	elif ((++late_update==5)); then
		update_ms=$((update_ms+100))
		draw_update_string
	fi
	
	if ((skip_process_draw==1)); then unset skip_process_draw; fi
}

#? Pre main loop

#* Read config file or create if non existant
config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/bashtop"
if [[ -d "${config_dir}" && -w "${config_dir}" ]] || mkdir -p "${config_dir}"; then 
	theme_dir="${config_dir}/themes"
	if [[ ! -d "${theme_dir}" ]]; then mkdir -p "${theme_dir}"; fi
	config_file="${config_dir}/bashtop.cfg"
	# shellcheck source=/dev/null
	if [[ -e "$config_file" ]]; then
		source "$config_file"

		#* If current config is from an older version recreate config file and save user changes
		if [[ $(get_value -sf "${config_file}" -k "bashtop v." -mk 1) != "${version}" ]]; then
			create_config
			save_config "${save_array[@]}"
		fi
	else create_config; fi
else
	#* If anything goes wrong turn off all writing to filesystem
	echo "ERROR: Could not set config dir!"
	config_dir="/dev/null"
	config_file="/dev/null"
	error_logging="false"
	unset 'save_array[@]'
fi

#* Set up traps for ctrl-c, soft kill, window resize, ctrl-z and resume from ctrl-z
trap 'quitting=1; time_left=0' SIGINT SIGQUIT SIGTERM
trap 'resized=1; time_left=0' SIGWINCH
trap 'sleepy=1; time_left=0' SIGTSTP 
trap 'resume_' SIGCONT



#* Set up error logging to file if enabled
if [[ $error_logging == true ]]; then
	set -o errtrace
	trap 'traperr' ERR

	#* Remove everything but the last 500 lines of error log if larger than 500 lines
	if [[ -e "${config_dir}/error.log" && $(wc -l <"${config_dir}/error.log") -gt 500 ]]; then
		tail -n 500 "${config_dir}/error.log" > "${config_dir}/tmp"
		rm "${config_dir}/error.log"
		mv "${config_dir}/tmp" "${config_dir}/error.log"
	fi
	( echo " " ; echo "New instance of bashtop version: ${version} Pid: $$" ) >> "${config_dir}/error.log"
	exec 2>>"${config_dir}/error.log"
	if [[ $1 == "--debug" ]]; then
		exec 19>"${config_dir}/tracing.log"
		BASH_XTRACEFD=19
		set -x
	fi
else
	exec 2>/dev/null
fi

#* Call init function
init_

#* Start infinite loop
until false; do main_loop; done

#* Quit cleanly even if false starts being true...
quit_
