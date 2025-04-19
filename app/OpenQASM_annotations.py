import requests
import pandas as pd
import os
QPROV_URL = os.getenv('QPROV_URL', 'http://qprov:5020/qprov')
class Circuit_Provenance:
    def __init__(self, backend, transpiled_circuit):
        self.backend = backend
        self.transpiled_circuit = transpiled_circuit


    def check_annotations(self, qasm_string):
            results = {}
            
            if "@get_qubit_characteristics" in qasm_string:
                results["qubit_characteristics"] = self.get_qubit_characteristics(self.backend, self.transpiled_circuit)
                
            if "@get_gate_characteristics" in qasm_string:
                results["gate_characteristics"] = self.get_gate_characteristics(self.backend, self.transpiled_circuit)
                
            if "@get_qpu" in qasm_string:
                results["quantum_computer"] = self.get_qpu_provenance(self.backend)

            if "@get_calibration_matrix" in qasm_string:
                results["calibration_matrix"] = self.get_calibration_matrix(self.backend)
                
            return results
    

    def get_qpu_url(self,backend):
            r = requests.get(f"{QPROV_URL}/providers")
            r.raise_for_status()
            providers = r.json()["_embedded"]["providerDtoes"]
            for provider in providers:
                if provider["name"] == "ibmq":
                    URL_for_qpu = provider["_links"]["qpus"]["href"]
                    get_available_qpu = requests.get(URL_for_qpu)
                    get_available_qpu.raise_for_status()
                    available_qpu = get_available_qpu.json()["_embedded"]["qpuDtoes"]
                    for qpu in available_qpu:
                        if qpu["name"] == backend:
                            return qpu["_links"]["self"]["href"]

#this method returns the list of physical qbits and the  list of  gates that has been used for transpilation 
#this method is exclusive for Qiskit. Consider changing it for other frameworks.
    def transpiled_circuit_information(self,transpiled):
        used_qubits = set()    
        qubit_gates = {} 
        for instruction in transpiled.data:
            gate_name = instruction.operation.name
            qubits = instruction.qubits
            for qubit in qubits:
                physical_qubit = qubit._index 
                used_qubits.add(physical_qubit)
                gate_label = gate_name
                qubit_gates.setdefault(physical_qubit, set()).add(gate_label)
        return sorted(list(used_qubits)), qubit_gates

#returns only a list of physical qbits that has been used for transpilation 
    def get_physical_qubits(self,transpiled):
        qubits = self.transpiled_circuit_information(transpiled)
        return qubits[0]

#returns a list of gates for a specific qubit
    def get_qubit_gates(self,transpiled, qubit):
        qubit_gates = self.transpiled_circuit_information(transpiled)
        qubit_gates= qubit_gates[1]
        if qubit in qubit_gates:
           return qubit_gates[qubit]
        return []

#List of complete QProv URLs for the qubit ID
    def get_qubit_ids(self,backend,transpiled):
        physical_qubits = self.get_physical_qubits(transpiled)
        r = requests.get(f"{self.get_qpu_url(backend)}/qubits")
        r.raise_for_status()
        qubits = r.json()["_embedded"]["qubitDtoes"]
        qubit_urls = []
        for qubit in qubits:
            physical_num = int(qubit['name'])
            if physical_num in physical_qubits:
                qubit_url = qubit["_links"]["self"]["href"]
                qubit_urls.append(qubit_url)
        return qubit_urls

#dictionary containing qubit names and their characteristics
    def get_qubit_characteristics(self,backend, transpiled):

        qubit_urls = self.get_qubit_ids(backend, transpiled)
        characteristics_dict = {}
        
        t1_times = []
        t2_times = []
        readout_errors = []
        
        for qubit_url in qubit_urls:
                r = requests.get(qubit_url)
                r.raise_for_status()
                qubit_name = f"qubit {r.json()['name']}"
                #url = f"{qubit_url}/characteristics"
                #r = requests.get(url)
                #r.raise_for_status()
                #characteristics = r.json()["_embedded"]["qubitCharacteristicsDtoes"][0]
                
                #t1_time = characteristics["t1Time"]
                #t2_time = characteristics["t2Time"]
                #readout_error = characteristics["readoutError"]
                
                #t1_times.append(t1_time)
                #t2_times.append(t2_time)
                #readout_errors.append(readout_error)
                
                characteristics_dict[qubit_name] = {
                  #  "t1_time": t1_time,
                #    "t2_time": t2_time,
                #    "readout_error": readout_error
                }
        
       # characteristics_dict["averages"] = {
           # "avg_t1_time": sum(t1_times) / len(t1_times),
           # "avg_t2_time": sum(t2_times) / len(t2_times),
           # "avg_readout_error": sum(readout_errors) / len(readout_errors)
        #}
        
        return characteristics_dict

    #dictionary containing qubit names and their gate characteristics
    def get_gate_characteristics(self,backend, transpiled):
        qubit_urls = self.get_qubit_ids(backend, transpiled)
        qubit_gate_characteristics = {}
        all_gate_times = []
        all_gate_fidelities = []
        
        for qubit_url in qubit_urls:
                r = requests.get(qubit_url)
                r.raise_for_status()
                qubit_name = f"qubit {r.json()['name']}"
                
                qubit_gate_characteristics[qubit_name] = {}
                qubit_gate_times = []
                qubit_gate_fidelities = []
                
                gates= self.get_qubit_gates(transpiled, int(qubit_name.split(' ')[1]))
                
                gates_url = f"{qubit_url}/gates"
                r = requests.get(gates_url)
                r.raise_for_status()
                available_gates = r.json()["_embedded"]["gateDtoes"]
                
                for gate in available_gates:
                    gate_name = gate["name"]
                    if gate_name in gates:
                    
                       # url = gates["_links"]["characteristics"]["href"]
                       # r = requests.get(url)
                       # r.raise_for_status()
                       # characteristics = r.json()["_embedded"]["gateCharacteristicsDtoes"][0]
                        
                        #gate_time = characteristics["gateTime"]
                        #gate_fidelity = characteristics["gateFidelity"]
                        qubit_gate_characteristics[qubit_name][gate_name] = {
                         #   "gateTime": gate_time,
                        #    "gateFidelity": gate_fidelity
                        }
                        
                       # qubit_gate_times.append(gate_time)
                       # qubit_gate_fidelities.append(gate_fidelity)
                       # all_gate_times.append(gate_time)
                       # all_gate_fidelities.append(gate_fidelity)
                
                # Add per-qubit averages
                #if qubit_gate_times:  # Only add if the qubit has gates
                  #  qubit_gate_characteristics[qubit_name]["qubit_averages"] = {
                    #    "total_gate_time": sum(qubit_gate_times),
                    #    "avg_gate_fidelity": sum(qubit_gate_fidelities) / len(qubit_gate_fidelities)
                    #}
        
        # Add overall averages
        #if all_gate_times:  
           # qubit_gate_characteristics["overall_averages"] = {
            #    "avg_gate_time": sum(all_gate_times) / len(all_gate_times),
            #    "avg_gate_fidelity": sum(all_gate_fidelities) / len(all_gate_fidelities)
            #}
        
        return qubit_gate_characteristics

    #dictionary containing QPU name and its provenance metrics
    def get_qpu_provenance(self,backend):
        qpu_url = self.get_qpu_url(backend)
        r = requests.get(qpu_url)
        r.raise_for_status()
        qpu_data = r.json()
        provenance_metrics = {
            "name": qpu_data["name"],
            "avgT1Time": qpu_data["avgT1Time"],
            "avgT2Time": qpu_data["avgT2Time"],
            "avgReadoutError": qpu_data["avgReadoutError"],
            "avgMultiQubitGateError": qpu_data["avgMultiQubitGateError"],
            "avgSingleQubitGateError": qpu_data["avgSingleQubitGateError"],
            "avgMultiQubitGateTime": qpu_data["avgMultiQubitGateTime"],
            "avgSingleQubitGateTime": qpu_data["avgSingleQubitGateTime"],
            "maxGateTime": qpu_data["maxGateTime"]
        }
    
        return provenance_metrics

    #returns the calibration matrix for a specific quantum computer
    def get_calibration_matrix(self,backend):
        r = requests.get(f"{QPROV_URL}/providers")
        r.raise_for_status()
        providers = r.json()["_embedded"]["providerDtoes"]
        for provider in providers:
         if provider["name"] == "ibmq":
            URL_for_qpu = provider["_links"]["qpus"]["href"]
            get_available_qpu = requests.get(URL_for_qpu)
            get_available_qpu.raise_for_status()
            available_qpu = get_available_qpu.json()["_embedded"]["qpuDtoes"]
            for qpu in available_qpu:
                if qpu["name"] == backend:
                    aggregated_url = qpu["_links"]["aggregated-data"]["href"]
                    r = requests.get(aggregated_url)
                    r.raise_for_status()
                    
                    calibration_url = r.json()["_links"]["calibration-matrix"]["href"]
                    r = requests.get(calibration_url)
                    r.raise_for_status()
                    
                    calibration_data = r.json()["_embedded"]["calibrationMatrixDtoes"][0]
                    return calibration_data["calibrationMatrix"]
                
class Execution_Annotation:
    def check_execution_annotations(self, qasm_string, counts): 
        results = {}

        if "@reverse_bitString" in qasm_string:
            results['reverse_bitString'] = self.reverse_bitString(counts)
            
        if "@format_to_hex" in qasm_string:
            results['Hexadecimal representation'] = self.format_counts_hex(counts)
            
        if "@format_to_dec" in qasm_string:
            results['Decimal representation'] = self.format_counts_decimal(counts)
            
        return results

    def reverse_bitString(self, counts):
        reversed_counts = {}
        for bits, count in counts.items():
            reversed_bits = bits[::-1] 
            reversed_counts[reversed_bits] = count
        return reversed_counts
    
    def format_counts_hex(self, counts):
        hex_counts = {}
        for bitstring, count in counts.items():
            count_hex = hex(int(bitstring, 2))
            hex_counts[count_hex] = count
        return hex_counts

    def format_counts_decimal(self, counts):
        decimal_counts = {}
        for bitstring, count in counts.items():
            bit_length = len(bitstring)
            decimal = str(int(bitstring, 2))
            formatted_value = f"[{decimal}]-{bit_length} bits"
            decimal_counts[formatted_value] = count
        return decimal_counts
    


 
class QPU_Selection:


    # checking for annotation in th OpenQASM circuit.
    def check_qpu_annotations(self, qasm_string):
        for line in qasm_string.split('\n'):
            if '@select_qpu(' in line:
                first_split = line.split('@select_qpu(')
                comma_split = first_split[1].split(',')
                min_qubits = int(comma_split[0].strip())
                metric = comma_split[1].strip(')').strip()
                
                all_qpus = self.get_all_qpu()
                return self.select_qpu(min_qubits, metric, all_qpus)
                
    


    # getting all quantum computer from IBM only.
    def get_all_qpu(self):
        available_computer = []
        r = requests.get(f"{QPROV_URL}/providers")
        r.raise_for_status()
        providers = r.json()["_embedded"]["providerDtoes"]
        for provider in providers:
          if provider.get("name") =="ibmq": 
            provider_id = provider["id"]
            break
        qpu_r = requests.get(f"{QPROV_URL}/providers/{provider_id}/qpus")
        qpu_r.raise_for_status()
        qpus = qpu_r.json()["_embedded"]["qpuDtoes"]
        for qpu in qpus:
            collect_info = {
                'name': qpu['name'],
                'num_qubits': qpu.get('numberOfQubits'),
                'max_shots': qpu.get('maxShots'),
                'queue_size': qpu.get('queueSize'),
                'max_gate_time': qpu.get('maxGateTime'),
                't1_time': qpu.get('avgT1Time'),
                't2_time': qpu.get('avgT2Time'),
                'readout_error': qpu.get('avgReadoutError'),
                'multi_qubit_gate_error': qpu.get('avgMultiQubitGateError'),
                'single_qubit_gate_error': qpu.get('avgSingleQubitGateError'),
                'average_multi_qubit_gate_time': qpu.get('avgMultiQubitGateTime'),
                'average_single_qubit_gate_time': qpu.get('avgSingleQubitGateTime')
            }
            available_computer.append(collect_info)

        df = pd.DataFrame(available_computer)
        return df
    #filter operation based on number of qubits and user specified metric
    def select_qpu(self, min_qubits, metric, all_qpus):
        filtered_df = all_qpus[all_qpus['num_qubits'] >= min_qubits]
        if filtered_df.empty:
            return "No QPUs found with the specified number of qubits"
        if metric not in all_qpus.columns:
            return f"Unsupported metric: {metric}. Available metrics: {', '.join(all_qpus.columns)}"
        if metric == 't1_time' or metric == 't2_time':
            best_qpu = filtered_df.sort_values(metric, ascending=False).iloc[0]
        else:
            best_qpu = filtered_df.sort_values(metric, ascending=True).iloc[0]

        return best_qpu['name']