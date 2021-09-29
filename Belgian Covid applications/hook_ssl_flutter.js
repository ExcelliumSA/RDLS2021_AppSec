function hook_ssl_verify_result(address)
{
  Interceptor.attach(address, {
    onEnter: function(args) {
      console.log("Disabling SSL validation")
    },
    onLeave: function(retval)
    {
      console.log("Retval: " + retval)
      retval.replace(0x1);
  
    }
  });
}
function disablePinning(){
    // Change the offset on the line below with the binwalk result
    // If you are on 32 bit, add 1 to the offset to indicate it is a THUMB function.
    // Otherwise, you will get  'Error: unable to intercept function at ......; please file a bug'
    var address = Module.findBaseAddress('libflutter.so').add(0x5c6b7c)
    hook_ssl_verify_result(address);
}
setTimeout(disablePinning, 2000)